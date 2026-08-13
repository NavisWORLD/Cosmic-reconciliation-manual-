from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from .models import Event
from .store import MemoryStore


class Generator(Protocol):
    def __call__(self, messages: list[dict[str, str]], **kwargs: Any) -> str: ...


@dataclass(slots=True)
class AdapterConfig:
    recall_limit: int = 8
    dialogue_limit: int = 6
    lesson_limit: int = 8
    memory_char_budget: int = 6000


class MemoryAdapter:
    """Drop-in reconciliation wrapper around any callable text generator."""

    def __init__(self, store: MemoryStore, generator: Generator | None = None,
                 config: AdapterConfig | None = None):
        self.store = store
        self.generator = generator
        self.config = config or AdapterConfig()

    def build_context(self, query: str, session_id: str = "default") -> str:
        chunks: list[str] = []
        dialogue = self.store.recent_dialogue(session_id, self.config.dialogue_limit)
        if dialogue:
            chunks.append("RECENT DIALOGUE (oldest to newest):\n" + "\n".join(
                f"- user: {d['prompt']}\n  assistant: {d['response']}" for d in dialogue
            ))
        recalled = self.store.recall(query, self.config.recall_limit)
        if recalled:
            chunks.append("RELEVANT LONG-TERM MEMORY:\n" + "\n".join(
                f"- [{m.score:.3f}] {m.content}" for m in recalled
            ))
        lessons = self.store.lessons(self.config.lesson_limit)
        if lessons:
            chunks.append("CONSOLIDATED LESSONS:\n" + "\n".join(f"- {l['lesson']}" for l in lessons))
        return "\n\n".join(chunks)[: self.config.memory_char_budget]

    def prepare_messages(self, user_message: str, session_id: str = "default",
                         system_prompt: str | None = None) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        context = self.build_context(user_message, session_id)
        if context:
            messages.append({"role": "system", "content": "Persistent reconciliation context:\n" + context})
        messages.append({"role": "user", "content": user_message})
        return messages

    def turn(self, user_message: str, session_id: str = "default", system_prompt: str | None = None,
             generator: Generator | None = None, **kwargs: Any) -> str:
        gen = generator or self.generator
        if gen is None:
            raise ValueError("A generator callable is required")
        input_event = Event(source="chat", type="user_message", payload={"text": user_message}, session_id=session_id)
        self.store.append_event(input_event)
        messages = self.prepare_messages(user_message, session_id, system_prompt)
        response = str(gen(messages, **kwargs))
        output_event = Event(source="chat", type="assistant_message", payload={"text": response},
                             session_id=session_id, parent_hash=input_event.payload_hash)
        self.store.append_event(output_event)
        self.store.record_turn(user_message, response, session_id=session_id,
                               prompt_event_id=input_event.event_id, response_event_id=output_event.event_id)
        return response
