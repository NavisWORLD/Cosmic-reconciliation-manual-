# Cosmic Reconciliation Memory

**Portable durable memory, reconciliation loops, and teaching material derived from the COSMOS / CST project.**

Author / research lineage: **Cory Shane Davis**  
Foundational CST DOI: **10.5281/zenodo.17574447**

This repository turns the persistence architecture described in COSMOS into a small, model-agnostic library that another project can actually adopt. It is not tied to one LLM vendor, one operating system, one cloud, or one storage provider.

> **Engineering definition of “forever memory”**: durable, recoverable continuity across model calls, context truncation, process restarts, machine reboots, and portable-storage movement, until the owner explicitly deletes the data or the underlying storage fails. It does **not** mean physically infinite storage or perfect recall.

## What is included

- `cosmic_reconciliation.MemoryStore` — durable SQLite-backed event, dialogue, retrieval memory, lessons, adaptive weights, and organism/state storage.
- `MemoryAdapter` — wraps any callable model and injects relevant memory before generation, then persists the resulting turn.
- `Heartbeat` — fail-soft background maintenance/checkpoint loop.
- Portable USB / external-drive tooling with manifests, snapshots, and SHA-256 integrity verification.
- A dependency-free hashed-retrieval baseline, plus a hook for real embedding models.
- JSON schemas for interoperable events and portable-memory manifests.
- Manual, architecture guide, integration guide, USB guide, testing protocols, privacy/security notes, and teacher manual.
- Tests and GitHub Actions for Python 3.10–3.12.

## Install

```bash
python -m pip install -e .
```

Or from a cloned checkout:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -e . pytest
pytest -q
```

## Five-minute integration

```python
from cosmic_reconciliation import MemoryAdapter, MemoryStore


def my_model(messages, **kwargs):
    # Replace with Ollama, llama.cpp, an OpenAI-compatible client,
    # a custom transformer, or any other text generator.
    return "Your model response here"


store = MemoryStore("./memory/cosmos.db")
store.remember(
    "The project codename is Aurora.",
    tags=["project", "identity"],
    importance=0.95,
)

adapter = MemoryAdapter(store, my_model)
reply = adapter.turn(
    "What project are we working on?",
    session_id="cory",
    system_prompt="Answer using persistent memory when relevant.",
)
print(reply)
```

The adapter does four things:

1. stores the new input as an immutable event;
2. retrieves recent dialogue, relevant durable memories, and consolidated lessons;
3. injects a compact reconciliation context into the model call;
4. stores the response and dialogue record for the next turn.

## Make a portable memory USB

Any mounted directory works, so you can test before using real removable media:

```bash
cosmic-memory usb-init /path/to/drive
```

Windows example:

```powershell
cosmic-memory usb-init E:\
```

macOS example:

```bash
cosmic-memory usb-init /Volumes/MY_MEMORY
```

Linux example:

```bash
cosmic-memory usb-init /media/$USER/MY_MEMORY
```

The drive receives:

```text
COSMIC_MEMORY/
├── manifest.json
├── integrity.json
├── memory.db
├── snapshots/
└── exports/
```

Use it directly:

```python
from cosmic_reconciliation import MemoryStore
from cosmic_reconciliation.usb import memory_root

root = memory_root("E:\\")
store = MemoryStore(root / "memory.db")
```

Verify integrity:

```bash
cosmic-memory usb-verify E:\
```

Create a point-in-time database snapshot:

```bash
cosmic-memory usb-snapshot E:\
```

See **[USB_PORTABLE_MEMORY.md](docs/USB_PORTABLE_MEMORY.md)** for the complete workflow.

## Architecture in one loop

```text
experience
   ↓
immutable event
   ↓
recent dialogue + durable memory + lessons
   ↓
reconciliation context
   ↓
model / tool / agent
   ↓
response
   ↓
feedback / weights / state
   ↓
persist + checkpoint + optional replica
   ↓
restart / move drive / reconnect
   ↓
restore + recall
   ↺
```

The reusable idea is not “one magic memory database.” It is the separation of:

- **event memory** — what happened;
- **episodic/dialogue memory** — conversations in time;
- **retrieval memory** — information selected by relevance;
- **consolidated memory** — derived lessons that point back to evidence;
- **adaptive memory** — weights that change future routing/selection;
- **organism/state memory** — persistent system state.

## CLI

```text
cosmic-memory --db ./memory.db init
cosmic-memory --db ./memory.db remember "A durable fact" --tag project --importance 0.9
cosmic-memory --db ./memory.db recall "project"
cosmic-memory --db ./memory.db stats
cosmic-memory usb-init <path>
cosmic-memory usb-verify <path>
cosmic-memory usb-snapshot <path>
```

## Scientific / claim boundary

This repository publishes reproducible software patterns and research lineage. It does not claim that persistent memory proves consciousness, that 12D/54D labels are literal physical dimensions, or that quantum entropy automatically improves model intelligence. Those are separate empirical questions.

The public CST/COSMOS research lineage explicitly preserves positive results, null results, and mechanism failures. That discipline is retained here: **implemented** means a software mechanism exists; **measured** means a defined experiment produced a metric; **hypothesis** means it remains a question.

Read **[CLAIM_BOUNDARIES.md](docs/CLAIM_BOUNDARIES.md)** before citing the system scientifically.

## Documentation map

- [Full Reconciliation Manual](docs/MANUAL.md)
- [Teacher Manual / Course](docs/TEACHER_MANUAL.md)
- [Architecture Reference](docs/ARCHITECTURE.md)
- [Project Integration Guide](docs/INTEGRATION_GUIDE.md)
- [Portable USB Memory Guide](docs/USB_PORTABLE_MEMORY.md)
- [Security and Privacy](docs/SECURITY_PRIVACY.md)
- [Test and Recovery Protocols](docs/TEST_PROTOCOLS.md)
- [Research Lineage](docs/RESEARCH_LINEAGE.md)
- [Claim Boundaries](docs/CLAIM_BOUNDARIES.md)

## Licensing

Code and documentation in this repository are released under **Apache License 2.0**. See `LICENSE` and `NOTICE`.

The DOI identifies the foundational CST research deposit. A DOI is a citation/provenance identifier; it is not a substitute for the software license.

## Design rules

1. **Local first.** A cloud outage must not erase identity or memory.
2. **Append before summarize.** Preserve primary evidence before deriving lessons.
3. **Never silently overwrite history.** Consolidation creates derived records.
4. **Recall is bounded.** Do not dump an entire lifetime into every prompt.
5. **Fail soft.** Retrieval failure should not take down the model.
6. **Portable by ordinary tools.** SQLite + JSON + SHA-256 are deliberate choices.
7. **No secrets in memory.** Store API keys in a proper secret manager or environment configuration.
8. **Owner-controlled forgetting.** Persistence includes deletion and retention policy, not forced immortality.
9. **Test restart recovery.** A save is not proven until a clean process can restore it.
10. **Claims follow instrumentation.** Architecture language never substitutes for measurement.

---

Built as an open reconstruction of the Cosmic Reconciliation / Synaptic Persistence work so other developers, students, researchers, and local-model builders can study it, reproduce it, criticize it, and extend it.
