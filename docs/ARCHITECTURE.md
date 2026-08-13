# Architecture Reference

## Component map

```text
                    HUMAN / APPLICATION
                           │
                           ▼
                       INPUT EVENT
                           │
               ┌───────────┴───────────┐
               ▼                       ▼
        IMMUTABLE LEDGER          RECONCILIATION
                                       │
                        ┌──────────────┼──────────────┐
                        ▼              ▼              ▼
                   DIALOGUE       RETRIEVAL       LESSONS
                        └──────────────┼──────────────┘
                                       ▼
                                   GENERATOR
                                       │
                                       ▼
                                    RESPONSE
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
                  EVENT             WEIGHTS             STATE
                    └──────────────────┼──────────────────┘
                                       ▼
                                    SQLITE
                                       │
                           ┌───────────┴───────────┐
                           ▼                       ▼
                       SNAPSHOTS              USB / REPLICA
```

## Runtime contracts

### Event
Source evidence. Append-only.

### MemoryStore
Durable storage facade. Owns transactions and retrieval records.

### MemoryAdapter
Inference boundary. Retrieves memory before generation and persists the turn afterward.

### Heartbeat
Fail-soft periodic maintenance.

### Portable-memory functions
Filesystem layout, snapshotting, checksums, verification.

## Database guarantees

The reference store uses SQLite WAL mode and transactions. It is designed for a single active writer process. Applications needing high-concurrency distributed writes should implement the same logical schema in a server database while retaining export compatibility.

## Extension points

Custom embedding function, custom memory ranking, custom consolidation, model-specific generator callable, encryption wrapper, network replication, knowledge graph, multimodal metadata, access-control layer, and state/CNS integrations.

## Non-goals

The core package does not attempt to provide a foundation model, consciousness, biometric diagnosis, autonomous source-code mutation, a quantum computing service, secret management, or concurrent distributed database consensus.
