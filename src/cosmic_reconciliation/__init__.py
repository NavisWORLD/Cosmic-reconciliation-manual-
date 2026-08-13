"""Cosmic Reconciliation Memory: durable, model-agnostic persistence loops."""

from .adapter import AdapterConfig, MemoryAdapter
from .consolidation import simple_recurrence_consolidation
from .heartbeat import Heartbeat, HeartbeatConfig
from .models import Event, MemoryRecord, RecallResult
from .store import MemoryStore
from .usb import (
    initialize_portable_memory,
    restore_snapshot,
    snapshot_portable_memory,
    sync_database,
    verify_portable_memory,
    write_integrity_manifest,
)

__all__ = [
    "AdapterConfig",
    "MemoryAdapter",
    "Heartbeat",
    "HeartbeatConfig",
    "Event",
    "MemoryRecord",
    "RecallResult",
    "MemoryStore",
    "simple_recurrence_consolidation",
    "initialize_portable_memory",
    "snapshot_portable_memory",
    "sync_database",
    "restore_snapshot",
    "verify_portable_memory",
    "write_integrity_manifest",
]

__version__ = "1.1.0"
