# Cosmic Reconciliation Memory API Reference

This reference describes the public v1.1 API. The package is intentionally model-agnostic and dependency-light.

## `MemoryStore`

```python
from cosmic_reconciliation import MemoryStore
store = MemoryStore("./memory.db")
```

### Durable semantic memory

```python
memory_id = store.remember(
    "The project codename is Aurora",
    tags=["project"],
    importance=0.9,
    metadata={"source": "user"},
)
results = store.recall("project", limit=8)
record = store.get_memory(memory_id)
all_records = store.list_memories()
deleted = store.forget(memory_id)
```

`importance` is clamped to `[0, 1]`. The built-in retrieval baseline uses deterministic hashed token features and cosine similarity. Pass `embedding_fn=` to `MemoryStore` to replace it with a real embedding model.

### Event ledger

```python
from cosmic_reconciliation import Event

event = Event(
    source="chat",
    type="user_message",
    payload={"text": "hello"},
    session_id="session-1",
)
store.append_event(event)
```

Replaying the exact same event ID and content is idempotent. Reusing an existing `event_id` for different content raises `ValueError`.

### Dialogue persistence

```python
turn_id = store.record_turn(
    "hello",
    "hi",
    session_id="session-1",
    winning_agent="Cosmos",
    model_used="local-model",
)
recent = store.recent_dialogue("session-1", limit=8)
```

### Owner-controlled session deletion

```python
store.purge_session("session-1")
store.purge_session("session-1", hard_delete_events=True)
```

The first form deletes dialogue but leaves raw event records. The second explicitly deletes matching raw event records too.

### Consolidated lessons

```python
lesson_id = store.add_lesson(
    "Recurring project preference",
    evidence_ids=["memory-a", "memory-b"],
    score=0.8,
)
lessons = store.lessons(limit=12)
```

For the built-in transparent consolidation baseline:

```python
from cosmic_reconciliation import simple_recurrence_consolidation
created_ids = simple_recurrence_consolidation(store, min_occurrences=3)
```

The baseline is idempotent for an unchanged evidence set.

### Adaptive/model-trust weights

```python
new_value = store.update_weight(
    "router.logic",
    reward=1.0,
    learning_rate=0.08,
    decay=0.002,
)
weights = store.weights()
```

This is a persisted scalar adaptive layer, not transformer-weight training.

### Persistent application/organism state

```python
store.set_state("generation", 8)
value = store.get_state("generation")
```

Values are JSON-encoded in SQLite.

### Health and backup

```python
status = store.integrity_check()
store.checkpoint()
store.backup_to("./known-good.db")
```

`backup_to()` uses SQLite's backup API and is the supported way to copy an active WAL-backed store.

## `MemoryAdapter`

```python
from cosmic_reconciliation import MemoryAdapter

adapter = MemoryAdapter(store, generator=my_model)
reply = adapter.turn(
    "What are we building?",
    session_id="session-1",
    system_prompt="Use persistent memory when relevant.",
)
```

`generator` must be callable as:

```python
def generator(messages: list[dict[str, str]], **kwargs) -> str:
    ...
```

The adapter writes input/output events, attaches bounded memory context, calls the generator, and records the completed dialogue turn.

## `Heartbeat`

```python
from cosmic_reconciliation import Heartbeat, HeartbeatConfig

heartbeat = Heartbeat(
    store,
    HeartbeatConfig(interval_seconds=5.0, checkpoint_every=12),
    maintenance=lambda s: None,
)
heartbeat.start()
print(heartbeat.status())
heartbeat.stop()
```

`run_once()` is available for hosts that already own a scheduler and for deterministic tests. Maintenance errors are counted and retained in `last_error` instead of crashing the host loop.

## Portable memory API

```python
from cosmic_reconciliation import (
    initialize_portable_memory,
    sync_database,
    snapshot_portable_memory,
    restore_snapshot,
    verify_portable_memory,
)

initialize_portable_memory("/mounted/drive")
sync_database("./memory.db", "/mounted/drive")
snapshot_portable_memory("/mounted/drive", "known-good")
verify_portable_memory("/mounted/drive")
restore_snapshot("/mounted/drive", "known-good.db")
```

Portable storage is ordinary SQLite + JSON + SHA-256. The library does not encrypt the drive; use operating-system/full-volume encryption for sensitive data.
