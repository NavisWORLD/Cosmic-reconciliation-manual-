from __future__ import annotations

import json
import os
import sqlite3
import threading
from pathlib import Path
from typing import Any, Callable, Iterable

from .models import Event, MemoryRecord, RecallResult, utc_now
from .retrieval import cosine, hashed_embedding

EmbeddingFn = Callable[[str], list[float]]

_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY,
  timestamp TEXT NOT NULL,
  session_id TEXT NOT NULL,
  source TEXT NOT NULL,
  type TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  payload_hash TEXT NOT NULL,
  parent_hash TEXT,
  metadata_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS dialogue (
  turn_id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL,
  session_id TEXT NOT NULL,
  prompt TEXT NOT NULL,
  response TEXT NOT NULL,
  winning_agent TEXT NOT NULL,
  model_used TEXT NOT NULL,
  prompt_event_id TEXT,
  response_event_id TEXT
);
CREATE TABLE IF NOT EXISTS memories (
  memory_id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  content TEXT NOT NULL,
  tags_json TEXT NOT NULL,
  importance REAL NOT NULL,
  source_event_id TEXT,
  metadata_json TEXT NOT NULL,
  embedding_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS lessons (
  lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  lesson TEXT NOT NULL,
  evidence_json TEXT NOT NULL,
  score REAL NOT NULL,
  metadata_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS weights (
  key TEXT PRIMARY KEY,
  value REAL NOT NULL,
  updates INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS organism (
  key TEXT PRIMARY KEY,
  value_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
"""


class MemoryStore:
    """Durable local memory store using SQLite.

    The store is process-persistent, portable, inspectable, and model agnostic.
    It intentionally does not store API secrets.
    """

    def __init__(self, path: str | os.PathLike[str], embedding_fn: EmbeddingFn | None = None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.embedding_fn = embedding_fn or hashed_embedding
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._conn:
            self._conn.executescript(_SCHEMA)
            self._conn.execute("INSERT OR IGNORE INTO meta(key,value) VALUES('schema_version','1')")

    def close(self) -> None:
        with self._lock:
            self._conn.commit()
            self._conn.close()

    def __enter__(self) -> "MemoryStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def append_event(self, event: Event) -> str:
        with self._lock, self._conn:
            self._conn.execute(
                """INSERT OR IGNORE INTO events
                (event_id,timestamp,session_id,source,type,payload_json,payload_hash,parent_hash,metadata_json)
                VALUES(?,?,?,?,?,?,?,?,?)""",
                (event.event_id, event.timestamp, event.session_id, event.source, event.type,
                 json.dumps(event.payload, ensure_ascii=False), event.payload_hash, event.parent_hash,
                 json.dumps(event.metadata, ensure_ascii=False)),
            )
        return event.event_id

    def remember(self, content: str, tags: Iterable[str] = (), importance: float = 0.5,
                 source_event_id: str | None = None, metadata: dict[str, Any] | None = None) -> str:
        importance = max(0.0, min(1.0, float(importance)))
        record = MemoryRecord(content=content, tags=list(tags), importance=importance,
                              source_event_id=source_event_id, metadata=metadata or {})
        emb = self.embedding_fn(content)
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO memories VALUES(?,?,?,?,?,?,?,?)",
                (record.memory_id, record.created_at, record.content, json.dumps(record.tags), record.importance,
                 record.source_event_id, json.dumps(record.metadata, ensure_ascii=False), json.dumps(emb)),
            )
        return record.memory_id

    def recall(self, query: str, limit: int = 8, min_score: float = -1.0) -> list[RecallResult]:
        q = self.embedding_fn(query)
        with self._lock:
            rows = self._conn.execute("SELECT * FROM memories").fetchall()
        scored: list[RecallResult] = []
        for row in rows:
            score = cosine(q, json.loads(row["embedding_json"]))
            adjusted = score * 0.85 + float(row["importance"]) * 0.15
            if adjusted >= min_score:
                scored.append(RecallResult(
                    memory_id=row["memory_id"], content=row["content"], score=adjusted,
                    importance=float(row["importance"]), tags=json.loads(row["tags_json"]),
                    created_at=row["created_at"], metadata=json.loads(row["metadata_json"]),
                ))
        scored.sort(key=lambda r: (r.score, r.created_at), reverse=True)
        return scored[:max(1, int(limit))]

    def record_turn(self, prompt: str, response: str, session_id: str = "default",
                    winning_agent: str = "model", model_used: str = "",
                    prompt_event_id: str | None = None, response_event_id: str | None = None) -> int:
        with self._lock, self._conn:
            cur = self._conn.execute(
                """INSERT INTO dialogue(timestamp,session_id,prompt,response,winning_agent,model_used,prompt_event_id,response_event_id)
                VALUES(?,?,?,?,?,?,?,?)""",
                (utc_now(), session_id, prompt, response, winning_agent, model_used, prompt_event_id, response_event_id),
            )
            return int(cur.lastrowid)

    def recent_dialogue(self, session_id: str = "default", limit: int = 8) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM dialogue WHERE session_id=? ORDER BY turn_id DESC LIMIT ?",
                (session_id, max(1, int(limit))),
            ).fetchall()
        return [dict(r) for r in reversed(rows)]

    def add_lesson(self, lesson: str, evidence_ids: Iterable[str], score: float,
                   metadata: dict[str, Any] | None = None) -> int:
        with self._lock, self._conn:
            cur = self._conn.execute(
                "INSERT INTO lessons(created_at,lesson,evidence_json,score,metadata_json) VALUES(?,?,?,?,?)",
                (utc_now(), lesson, json.dumps(list(evidence_ids)), max(0.0, min(1.0, float(score))),
                 json.dumps(metadata or {}, ensure_ascii=False)),
            )
            return int(cur.lastrowid)

    def lessons(self, limit: int = 12) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM lessons ORDER BY score DESC, lesson_id DESC LIMIT ?", (max(1, int(limit)),)
            ).fetchall()
        return [dict(r) for r in rows]

    def update_weight(self, key: str, reward: float, learning_rate: float = 0.08,
                      decay: float = 0.002, minimum: float = 0.0, maximum: float = 1.0) -> float:
        reward = max(-1.0, min(1.0, float(reward)))
        with self._lock, self._conn:
            row = self._conn.execute("SELECT value,updates FROM weights WHERE key=?", (key,)).fetchone()
            old = float(row["value"]) if row else 0.5
            updates = int(row["updates"]) if row else 0
            new = (1.0 - decay) * old + learning_rate * reward
            new = max(minimum, min(maximum, new))
            self._conn.execute(
                """INSERT INTO weights(key,value,updates,updated_at) VALUES(?,?,?,?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value,updates=excluded.updates,updated_at=excluded.updated_at""",
                (key, new, updates + 1, utc_now()),
            )
        return new

    def weights(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM weights ORDER BY key").fetchall()
        return {r["key"]: {"value": r["value"], "updates": r["updates"], "updated_at": r["updated_at"]} for r in rows}

    def set_state(self, key: str, value: Any) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """INSERT INTO organism(key,value_json,updated_at) VALUES(?,?,?)
                ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json,updated_at=excluded.updated_at""",
                (key, json.dumps(value, ensure_ascii=False), utc_now()),
            )

    def get_state(self, key: str, default: Any = None) -> Any:
        with self._lock:
            row = self._conn.execute("SELECT value_json FROM organism WHERE key=?", (key,)).fetchone()
        return json.loads(row["value_json"]) if row else default

    def stats(self) -> dict[str, int]:
        names = ["events", "dialogue", "memories", "lessons", "weights", "organism"]
        with self._lock:
            return {n: int(self._conn.execute(f"SELECT COUNT(*) FROM {n}").fetchone()[0]) for n in names}

    def checkpoint(self) -> None:
        with self._lock:
            self._conn.execute("PRAGMA wal_checkpoint(FULL)")
            self._conn.commit()
