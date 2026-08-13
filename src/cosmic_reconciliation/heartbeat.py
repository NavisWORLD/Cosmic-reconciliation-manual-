from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Callable

from .store import MemoryStore


@dataclass(slots=True)
class HeartbeatConfig:
    interval_seconds: float = 5.0
    checkpoint_every: int = 12


class Heartbeat:
    """Small fail-soft maintenance loop for persistence/checkpoint work."""

    def __init__(self, store: MemoryStore, config: HeartbeatConfig | None = None,
                 maintenance: Callable[[MemoryStore], None] | None = None):
        self.store = store
        self.config = config or HeartbeatConfig()
        self.maintenance = maintenance
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="cosmic-memory-heartbeat", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout)

    def _run(self) -> None:
        tick = 0
        while not self._stop.wait(self.config.interval_seconds):
            tick += 1
            try:
                if self.maintenance:
                    self.maintenance(self.store)
                if tick % max(1, self.config.checkpoint_every) == 0:
                    self.store.checkpoint()
            except Exception:
                continue
