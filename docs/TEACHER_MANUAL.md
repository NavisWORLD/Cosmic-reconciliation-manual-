# Teacher Manual

## Teaching Cosmic Reconciliation Memory as reproducible systems engineering

### Audience

Advanced high-school, undergraduate, graduate, bootcamp, independent-research, or internal engineering teams with basic Python familiarity.

### Course objective

Students should finish the course able to build, test, criticize, and extend a persistent model-memory system without confusing storage, retrieval, learning, and scientific claims.

## Learning outcomes

Students will be able to:

1. distinguish model weights from external memory;
2. explain event, episodic, retrieval, consolidated, adaptive, and state memory;
3. implement restart-safe persistence;
4. integrate memory with a generator without vendor lock-in;
5. create and verify a portable memory drive;
6. design bounded retrieval instead of dumping all history into a prompt;
7. preserve source evidence through consolidation;
8. measure retrieval quality and recovery behavior;
9. identify privacy and memory-poisoning risks;
10. distinguish implemented mechanisms, measurements, nulls, hypotheses, and metaphor.

## Suggested 12-week course

### Week 1 — Why model context is not memory

Topics: context windows, process state, persistence, model parameters vs external state.

Lab: create a Python variable, restart the process, observe loss; then repeat using SQLite.

### Week 2 — Event sourcing

Topics: immutable events, timestamps, content hashes, lineage.

Lab: record 100 events and verify payload hashes.

### Week 3 — Dialogue memory

Topics: chronological recall, session identity, recency traps, deduplication.

Lab: record/recover conversation turns after restart.

### Week 4 — Retrieval

Topics: lexical search, feature hashing, embeddings, cosine similarity, Recall@K / MRR.

Lab: compare the built-in hashed baseline with a chosen embedding model.

### Week 5 — Reconciliation prompts

Topics: context budgeting, provenance, conflicts, hallucinated memories.

Lab: wrap a simple local or mock generator with `MemoryAdapter`.

### Week 6 — Consolidation

Topics: primary vs derived memory, evidence links, summarization errors, idempotence.

Lab: create recurring tagged memories and generate derived lessons.

### Week 7 — Adaptive weights

Topics: reward, bounded updates, decay, routing.

Lab: simulate two models and learn which performs better on a frozen task set.

### Week 8 — Persistent state

Topics: state machines, EMA-like updates, relationship/project state, why state is not fact memory.

Lab: persist application state and restore it after restart.

### Week 9 — Heartbeat and maintenance

Topics: reactive vs background loops, fail-soft maintenance, checkpoints, health probes.

Lab: attach a maintenance callback that periodically checkpoints and logs stats.

### Week 10 — Portable memory drives

Topics: filesystem portability, SQLite on removable media, checksums, safe eject, backup vs portability.

Lab: initialize a portable-memory directory, then repeat on a real removable drive if available.

### Week 11 — Security, privacy, and poisoning

Topics: secret handling, encryption at rest, prompt injection, untrusted memory, deletion/retention.

Lab: design metadata labels for trusted, untrusted, verified, and derived records.

### Week 12 — Reproducibility and CST/COSMOS lineage

Topics: claim taxonomy, dynamic-state experiments, null results, conceptual language vs operational mechanism.

Final lab: run a clean-room persistence demonstration from a blank environment.

## Core labs

### Lab A — Restart proof

Pass criteria: unique memory written; process ends; new process retrieves it; no in-memory Python object from the first process is reused.

### Lab B — Memory ranking

Create at least 50 records across five topics. Write 20 query/expected-topic pairs. Measure Recall@3. Students must report failures, not only successes.

### Lab C — Portable drive

Initialize drive, write five memories, create snapshot, unmount, remount, verify hashes, retrieve records.

### Lab D — Poisoning

Insert a false/untrusted memory and a verified contradictory record. Extend ranking/prompt policy so the model can see provenance and refuses to silently merge the claims.

### Lab E — Adaptive router

Use deterministic mock models with different task strengths. Update weights after each task. Plot or tabulate the learned values over time.

## Oral examination questions

1. Why is saving every chat turn insufficient for useful memory?
2. Why should primary events be immutable?
3. What is the difference between a lesson and its evidence?
4. Why can a large memory store coexist with a small context window?
5. What does “fail soft” mean in the inference path?
6. Why is a successful save not enough to prove persistence?
7. What problem does a portable manifest solve?
8. What does a SHA-256 integrity file prove, and what does it not prove?
9. Why is adaptive model trust different from transformer attention?
10. Why does persistent state not prove consciousness?
11. Why should null experimental results be published?
12. What is dangerous about storing raw biometrics by default?

## Answer key / grading notes

1. Useful recall requires selection and reinjection before inference.
2. Immutability preserves provenance and makes corrections auditable.
3. Lesson is derived; evidence is primary. The lesson may be wrong.
4. External retrieval selects a small relevant subset.
5. Auxiliary failure is isolated; the core model can still respond.
6. A fresh process must recover the data.
7. It declares format/version/database/security metadata for portability.
8. It detects content changes relative to the recorded digest; it does not encrypt or authenticate the owner by itself.
9. Trust weights are persistent routing policy; attention is an inference mechanism inside a model.
10. Continuity is observable software behavior; subjective experience is not measured by persistence alone.
11. Nulls constrain claims and prevent repeating failed mechanisms as facts.
12. Privacy, consent, breach impact, and inference/diagnostic overreach.

## Assessment rubric

### Excellent

- mechanism is reproduced from a clean environment;
- restart and recovery tests pass;
- student distinguishes all memory classes;
- retrieval is measured on a frozen query set;
- limitations are explicit;
- no consciousness/quantum/sensory overclaims;
- privacy threat model is credible.

### Needs revision

- demos only within one process;
- calls all stored data memory without separation;
- no source IDs for derived lessons;
- no retrieval metric;
- assumes a USB copy is automatically secure;
- uses architecture labels as scientific proof.

## Capstone

Build a small persistent assistant with one local or mock generator, persistent event/dialogue store, retrieval memory, one consolidation method, one adaptive weight, one persistent state value, heartbeat checkpointing, portable-drive export/use, restart proof, and a written claim boundary.

Students submit source, test output, database schema explanation, and a five-minute live restart demonstration.
