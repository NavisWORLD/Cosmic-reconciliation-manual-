from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict

from .retrieval import tokenize
from .store import MemoryStore


def _dedupe_key(tag: str, evidence_ids: list[str]) -> str:
    payload = json.dumps(
        {"method": "simple_recurrence_consolidation", "tag": tag, "evidence": sorted(evidence_ids)},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _existing_dedupe_keys(store: MemoryStore) -> set[str]:
    keys: set[str] = set()
    for row in store.lessons(limit=10000):
        try:
            metadata = json.loads(row.get("metadata_json") or "{}")
        except (TypeError, json.JSONDecodeError):
            continue
        key = metadata.get("dedupe_key")
        if key:
            keys.add(str(key))
    return keys


def simple_recurrence_consolidation(
    store: MemoryStore,
    min_occurrences: int = 3,
    max_lessons: int = 6,
) -> list[int]:
    """Create evidence-linked recurring-theme lessons without overwriting memory.

    This baseline is intentionally transparent and deterministic. Re-running it
    against unchanged source memories is idempotent: a lesson with the same tag
    and exact evidence set will not be emitted twice.
    """
    by_tag: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for row in store.list_memories():
        for tag in row.get("tags", []):
            by_tag[str(tag).lower()].append((str(row["memory_id"]), str(row["content"])))

    existing = _existing_dedupe_keys(store)
    created: list[int] = []
    for tag, items in sorted(by_tag.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        if len(items) < max(1, int(min_occurrences)):
            continue
        evidence_ids = [i for i, _ in items]
        key = _dedupe_key(tag, evidence_ids)
        if key in existing:
            continue

        tokens = Counter(t for _, content in items for t in tokenize(content) if len(t) > 3)
        common = ", ".join(w for w, _ in tokens.most_common(5))
        lesson = (
            f"Recurring memory theme '{tag}' appears {len(items)} times"
            + (f"; common terms: {common}." if common else ".")
        )
        score = min(1.0, 0.4 + 0.1 * len(items))
        created.append(
            store.add_lesson(
                lesson,
                evidence_ids,
                score,
                {
                    "method": "simple_recurrence_consolidation",
                    "tag": tag,
                    "dedupe_key": key,
                },
            )
        )
        existing.add(key)
        if len(created) >= max(1, int(max_lessons)):
            break
    return created
