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
CREATE INDEX IF NOT EXISTS idx_events_session_time ON events(session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_dialogue_session_turn ON dialogue(session_id, turn_id);
CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at);
CREATE INDEX IF NOT EXISTS idx_lessons_score ON lessons(score, lesson_id);
"""


class MemoryStore:
    """Durable local memory store using SQLite.

    The store is process-persistent, portable, inspectable, and model agnostic.
    It intentionally does not store API secrets. SQLite WAL is used for normal
    operation; ``backup_to`` is the supported way to make a transaction-safe
    portable copy while the store is active.
    """

    def __init__(self, path: str | os.PathLike[str], embedding_fn: EmbeddingFn | None = None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.embedding_fn = embedding_fn or hashed_embedding
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False, timeout=30.0)
        self._conn.row_factory = sqlite3.Row
        with self._conn:
            self._conn.execute("PRAGMA busy_timeout=5000")
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
        """Append an event without silently accepting an ID collision.

        Replaying the exact same event is idempotent. Reusing an existing
        ``event_id`` for different content is rejected because that would make
        an audit trail ambiguous.
        """
        with self._lock, self._conn:
            existing = self._conn.execute(
                "SELECT payload_hash,session_id,source,type FROM events WHERE event_id=?",
                (event.event_id,),
            ).fetchone()
            if existing is not None:
                same = (
                    existing["payload_hash"] == event.payload_hash
                    and existing["session_id"] == event.session_id
                    and existing["source"] == event.source
                    and existing["type"] == event.type
                )
                if not same:
                    raise ValueError(f"event_id collision for {event.event_id}")
                return event.event_id
            self._conn.execute(
                """INSERT INTO events
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

    def get_memory(self, memory_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute("SELECT * FROM memories WHERE memory_id=?", (memory_id,)).fetchone()
        return self._memory_row(row) if row else None

    def list_memories(self, limit: int | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM memories ORDER BY created_at, memory_id"
        params: tuple[Any, ...] = ()
        if limit is not None:
            sql += " LIMIT ?"
            params = (max(1, int(limit)),)
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        return [self._memory_row(row) for row in rows]

    @staticmethod
    def _memory_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["tags"] = json.loads(data.pop("tags_json"))
        data["metadata"] = json.loads(data.pop("metadata_json"))
        data["embedding"] = json.loads(data.pop("embedding_json"))
        return data

    def forget(self, memory_id: str) -> bool:
        """Explicitly delete one durable semantic memory by ID."""
        with self._lock, self._conn:
            cur = self._conn.execute("DELETE FROM memories WHERE memory_id=?", (memory_id,))
        return bool(cur.rowcount)

    def purge_session(self, session_id: str, *, hard_delete_events: bool = False) -> dict[str, int]:
        """Delete dialogue for a session and optionally its raw event records.

        Event deletion is opt-in because the event table is intended as an
        audit ledger. Privacy-sensitive deployments may choose the hard-delete
        path explicitly.
        """
        with self._lock, self._conn:
            dialogue = self._conn.execute("DELETE FROM dialogue WHERE session_id=?", (session_id,)).rowcount
            events = 0
            if hard_delete_events:
                events = self._conn.execute("DELETE FROM events WHERE session_id=?", (session_id,)).rowcount
        return {"dialogue": int(dialogue), "events": int(events)}

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

    def integrity_check(self) -> dict[str, Any]:
        """Run SQLite's own consistency check and return a structured result."""
        with self._lock:
            rows = [str(r[0]) for r in self._conn.execute("PRAGMA integrity_check").fetchall()]
        return {"ok": rows == ["ok"], "messages": rows}

    def checkpoint(self) -> None:
        with self._lock:
            self._conn.execute("PRAGMA wal_checkpoint(FULL)")
            self._conn.commit()

    def backup_to(self, destination: str | os.PathLike[str]) -> Path:
        """Create a transaction-consistent SQLite backup, including WAL state."""
        dest = Path(destination)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            self._conn.commit()
            target = sqlite3.connect(dest, timeout=30.0)
            try:
                self._conn.backup(target)
                target.commit()
            finally:
                target.close()
        return dest
