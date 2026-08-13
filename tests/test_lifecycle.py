import pytest

from cosmic_reconciliation import Event, MemoryStore


def test_state_weight_and_forget_survive_restart(tmp_path):
    db = tmp_path / "memory.db"
    with MemoryStore(db) as store:
        memory_id = store.remember("portable memory survives", tags=["continuity"], importance=0.9)
        store.set_state("organism", {"generation": 8, "valence": 0.25})
        learned = store.update_weight("DeepSeek.logic", reward=1.0, learning_rate=0.1, decay=0.0)
        assert learned == pytest.approx(0.6)
        assert store.integrity_check()["ok"] is True

    with MemoryStore(db) as store:
        assert store.get_state("organism")["generation"] == 8
        assert store.weights()["DeepSeek.logic"]["updates"] == 1
        assert store.get_memory(memory_id)["content"] == "portable memory survives"
        assert store.forget(memory_id) is True
        assert store.forget(memory_id) is False

    with MemoryStore(db) as store:
        assert store.get_memory(memory_id) is None
        assert store.integrity_check()["ok"] is True


def test_event_replay_is_idempotent_but_collision_is_rejected(tmp_path):
    db = tmp_path / "events.db"
    event = Event(source="chat", type="user_message", payload={"text": "hello"}, event_id="fixed-id")
    with MemoryStore(db) as store:
        assert store.append_event(event) == "fixed-id"
        assert store.append_event(event) == "fixed-id"
        conflicting = Event(source="chat", type="user_message", payload={"text": "different"}, event_id="fixed-id")
        with pytest.raises(ValueError):
            store.append_event(conflicting)


def test_purge_session_can_preserve_or_delete_raw_events(tmp_path):
    db = tmp_path / "purge.db"
    with MemoryStore(db) as store:
        e1 = Event(source="chat", type="user_message", payload={"text": "one"}, session_id="s1")
        e2 = Event(source="chat", type="assistant_message", payload={"text": "two"}, session_id="s1")
        store.append_event(e1)
        store.append_event(e2)
        store.record_turn("one", "two", session_id="s1", prompt_event_id=e1.event_id, response_event_id=e2.event_id)
        result = store.purge_session("s1")
        assert result == {"dialogue": 1, "events": 0}
        assert store.stats()["events"] == 2
        result = store.purge_session("s1", hard_delete_events=True)
        assert result["events"] == 2
        assert store.stats()["events"] == 0
