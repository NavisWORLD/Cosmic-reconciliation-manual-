from cosmic_reconciliation import MemoryAdapter, MemoryStore


def test_adapter_injects_context_and_records_turn(tmp_path):
    seen = {}
    def gen(messages, **_):
        seen["messages"] = messages
        return "ok"
    with MemoryStore(tmp_path / "a.db") as store:
        store.remember("Remember the lighthouse.", ["symbol"], 1.0)
        adapter = MemoryAdapter(store, gen)
        assert adapter.turn("What should I remember?", session_id="u") == "ok"
        assert any("lighthouse" in m["content"] for m in seen["messages"])
        assert store.stats()["dialogue"] == 1
