from cosmic_reconciliation import MemoryAdapter, MemoryStore


def demo_model(messages, **_):
    # Replace this with your local/cloud LLM call.
    user = messages[-1]["content"]
    return f"Demo response to: {user}"


with MemoryStore("./demo_memory.db") as store:
    store.remember("The project name is Aurora.", tags=["project"], importance=0.9)
    adapter = MemoryAdapter(store, demo_model)
    print(adapter.turn("What are we building?", session_id="alice"))
