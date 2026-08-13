from cosmic_reconciliation import MemoryStore
from cosmic_reconciliation.usb import initialize_portable_memory, memory_root, restore_snapshot, snapshot_portable_memory, sync_database, verify_portable_memory


def test_portable_memory_sync_snapshot_and_recovery(tmp_path):
    local_db = tmp_path / "local.db"
    portable_dir = tmp_path / "portable"

    with MemoryStore(local_db) as store:
        store.remember("The portable project is Aurora", tags=["project"], importance=0.95)
        store.set_state("generation", 8)
        store.update_weight("router.logic", 1.0)

    initialize_portable_memory(portable_dir)
    sync_database(local_db, portable_dir, overwrite=True)
    assert verify_portable_memory(portable_dir)["ok"] is True

    portable_db = memory_root(portable_dir) / "memory.db"
    with MemoryStore(portable_db) as store:
        assert store.recall("Aurora", 1)[0].content == "The portable project is Aurora"
        assert store.get_state("generation") == 8
        assert "router.logic" in store.weights()

    snapshot = snapshot_portable_memory(portable_dir, "known-good")
    with MemoryStore(portable_db) as store:
        store.remember("new later note", tags=["later"])

    restore_snapshot(portable_dir, snapshot.name)
    with MemoryStore(portable_db) as store:
        contents = [m["content"] for m in store.list_memories()]
        assert "The portable project is Aurora" in contents
        assert "new later note" not in contents

    assert verify_portable_memory(portable_dir)["ok"] is True
