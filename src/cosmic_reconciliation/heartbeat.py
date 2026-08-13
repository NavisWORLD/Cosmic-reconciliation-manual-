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
    """Small fail-soft maintenance loop for persistence/checkpoint work.

    The loop is deliberately boring and observable: maintenance errors are
    recorded instead of raised into the caller, while counters make it possible
    to verify that the loop is alive. ``run_once`` exists for tests and for
    hosts that already own their own scheduler.
    """

    def __init__(self, store: MemoryStore, config: HeartbeatConfig | None = None,
                 maintenance: Callable[[MemoryStore], None] | None = None):
        self.store = store
        self.config = config or HeartbeatConfig()
        self.maintenance = maintenance
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.ticks = 0
        self.checkpoints = 0
        self.errors = 0
        self.last_error: str | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="cosmic-memory-heartbeat", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0, final_checkpoint: bool = True) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout)
        if final_checkpoint:
            try:
                self.store.checkpoint()
                self.checkpoints += 1
            except Exception as exc:  # fail-soft by design
                self.errors += 1
                self.last_error = f"{type(exc).__name__}: {exc}"

    def status(self) -> dict[str, object]:
        return {
            "running": bool(self._thread and self._thread.is_alive()),
            "ticks": self.ticks,
            "checkpoints": self.checkpoints,
            "errors": self.errors,
            "last_error": self.last_error,
        }

    def run_once(self) -> None:
        self.ticks += 1
        try:
            if self.maintenance:
                self.maintenance(self.store)
            if self.ticks % max(1, int(self.config.checkpoint_every)) == 0:
                self.store.checkpoint()
                self.checkpoints += 1
            self.last_error = None
        except Exception as exc:  # fail-soft by design
            self.errors += 1
            self.last_error = f"{type(exc).__name__}: {exc}"

    def _run(self) -> None:
        interval = max(0.01, float(self.config.interval_seconds))
        while not self._stop.wait(interval):
            self.run_once()
