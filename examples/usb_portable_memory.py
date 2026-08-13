from cosmic_reconciliation import MemoryStore, initialize_portable_memory, verify_portable_memory

# Point this at a mounted USB drive or any ordinary directory.
root = initialize_portable_memory("./portable_demo")
with MemoryStore(root / "memory.db") as store:
    store.remember("This memory travels with the drive.", tags=["portable"], importance=1.0)
    store.checkpoint()

print(verify_portable_memory("./portable_demo"))
