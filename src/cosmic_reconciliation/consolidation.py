from __future__ import annotations

from collections import Counter, defaultdict

from .retrieval import tokenize
from .store import MemoryStore


def simple_recurrence_consolidation(store: MemoryStore, min_occurrences: int = 3, max_lessons: int = 6) -> list[int]:
    """Transparent baseline consolidation that never overwrites primary memory."""
    rows = store._conn.execute("SELECT memory_id,tags_json,content FROM memories").fetchall()
    import json
    by_tag: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for row in rows:
        for tag in json.loads(row["tags_json"]):
            by_tag[str(tag).lower()].append((row["memory_id"], row["content"]))
    created: list[int] = []
    for tag, items in sorted(by_tag.items(), key=lambda kv: len(kv[1]), reverse=True):
        if len(items) < min_occurrences:
            continue
        tokens = Counter(t for _, content in items for t in tokenize(content) if len(t) > 3)
        common = ", ".join(w for w, _ in tokens.most_common(5))
        lesson = f"Recurring memory theme '{tag}' appears {len(items)} times" + (f"; common terms: {common}." if common else ".")
        score = min(1.0, 0.4 + 0.1 * len(items))
        created.append(store.add_lesson(lesson, [i for i, _ in items], score,
                                        {"method": "simple_recurrence_consolidation", "tag": tag}))
        if len(created) >= max_lessons:
            break
    return created
