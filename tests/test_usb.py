from cosmic_reconciliation import MemoryStore, initialize_portable_memory, snapshot_portable_memory, verify_portable_memory
from cosmic_reconciliation.usb import write_integrity_manifest


def test_usb_memory(tmp_path):
    root = initialize_portable_memory(tmp_path)
    with MemoryStore(root / "memory.db") as store:
        store.remember("portable fact", ["usb"], 1.0)
        store.checkpoint()
    write_integrity_manifest(root)
    assert verify_portable_memory(tmp_path)["ok"] is True
    snap = snapshot_portable_memory(tmp_path, "test")
    assert snap.exists()
