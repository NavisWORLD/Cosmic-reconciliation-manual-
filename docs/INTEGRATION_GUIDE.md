# Integration Guide

## Pattern A: Wrap a chat model

```python
from cosmic_reconciliation import MemoryAdapter, MemoryStore

store = MemoryStore("memory.db")

def generate(messages, **kwargs):
    return your_client.chat(messages)

memory_model = MemoryAdapter(store, generate)
answer = memory_model.turn("Continue the design from last time", session_id="user-123")
```

## Pattern B: Only use retrieval

```python
store = MemoryStore("memory.db")
context = store.recall("database migration", limit=5)
```

## Pattern C: Store tool outcomes

```python
memory_id = store.remember(
    "Build 418 failed because port 8765 was already occupied.",
    tags=["build", "failure", "port-8765"],
    importance=0.85,
    metadata={"build": 418, "exit_code": 1},
)
```

## Pattern D: Persist adaptive routing

```python
score = store.update_weight("coder_model.python", reward=1.0)
```

## Pattern E: Persist application state

```python
store.set_state("active_project", {"name": "Aurora", "phase": 3})
project = store.get_state("active_project")
```

## Pattern F: Portable user-owned memory

```python
from cosmic_reconciliation.usb import initialize_portable_memory
from cosmic_reconciliation import MemoryStore

root = initialize_portable_memory("/Volumes/ALICE_MEMORY")
store = MemoryStore(root / "memory.db")
```

## Scope isolation

Use distinct `session_id` values and, for multi-user products, add application-level authorization. The reference library is a storage primitive, not an identity provider.

## Prompt policy

Do not inject all memories. Retrieve a small set and impose a character/token budget.

```text
The following block is retrieved memory. Use it only when relevant. Do not invent additional memories. If two records conflict, say so.
```

## Migration from an existing memory system

1. export source records;
2. map stable source IDs into metadata;
3. insert raw memories before derived summaries;
4. preserve original timestamps when possible;
5. rebuild embeddings using one consistent model;
6. test recall on a known question set;
7. only then switch production reads.
