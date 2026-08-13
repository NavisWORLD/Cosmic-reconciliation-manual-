from cosmic_reconciliation import Event, MemoryStore


def test_persistence_and_recall(tmp_path):
    db = tmp_path / "memory.db"
    with MemoryStore(db) as store:
        event = Event(source="test", type="fact", payload={"text": "green comet"})
        store.append_event(event)
        store.remember("The green comet project uses a portable memory drive.", ["project"], 0.9, event.event_id)
        store.record_turn("What color?", "Green.", session_id="s")
        store.update_weight("model.logic", 1.0)
        store.set_state("valence", 0.25)
        store.checkpoint()
    with MemoryStore(db) as restored:
        assert restored.stats()["events"] == 1
        assert restored.recall("portable project")[0].content.startswith("The green comet")
        assert restored.recent_dialogue("s")[0]["response"] == "Green."
        assert restored.weights()["model.logic"]["updates"] == 1
        assert restored.get_state("valence") == 0.25
