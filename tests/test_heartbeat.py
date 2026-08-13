from cosmic_reconciliation import Heartbeat, HeartbeatConfig, MemoryStore


def test_heartbeat_run_once_and_checkpoint_accounting(tmp_path):
    db = tmp_path / "memory.db"
    calls = []

    def maintenance(store):
        calls.append(store.stats()["memories"])
        store.set_state("heartbeat_seen", len(calls))

    with MemoryStore(db) as store:
        hb = Heartbeat(store, HeartbeatConfig(interval_seconds=1.0, checkpoint_every=2), maintenance)
        hb.run_once()
        assert hb.status()["ticks"] == 1
        assert hb.status()["checkpoints"] == 0
        assert store.get_state("heartbeat_seen") == 1

        hb.run_once()
        status = hb.status()
        assert status["ticks"] == 2
        assert status["checkpoints"] == 1
        assert status["errors"] == 0
        assert calls == [0, 0]


def test_heartbeat_is_fail_soft(tmp_path):
    db = tmp_path / "memory.db"

    def broken(_store):
        raise RuntimeError("maintenance failed")

    with MemoryStore(db) as store:
        hb = Heartbeat(store, HeartbeatConfig(checkpoint_every=1), broken)
        hb.run_once()
        status = hb.status()
        assert status["ticks"] == 1
        assert status["errors"] == 1
        assert "RuntimeError" in str(status["last_error"])
