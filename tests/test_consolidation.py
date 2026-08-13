from cosmic_reconciliation import MemoryStore, simple_recurrence_consolidation


def test_recurrence_consolidation_is_idempotent(tmp_path):
    db = tmp_path / "memory.db"
    with MemoryStore(db) as store:
        for text in ["Aurora memory alpha", "Aurora memory beta", "Aurora memory gamma"]:
            store.remember(text, tags=["project"], importance=0.8)

        first = simple_recurrence_consolidation(store, min_occurrences=3)
        second = simple_recurrence_consolidation(store, min_occurrences=3)

        assert len(first) == 1
        assert second == []
        lessons = store.lessons(limit=10)
        assert len(lessons) == 1
        assert "Recurring memory theme 'project'" in lessons[0]["lesson"]

        store.remember("Aurora memory delta", tags=["project"], importance=0.8)
        third = simple_recurrence_consolidation(store, min_occurrences=3)
        assert len(third) == 1
        assert len(store.lessons(limit=10)) == 2
