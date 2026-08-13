# Test and Recovery Protocols

## PERSISTENCE-001 — restart recall

Write a unique memory, checkpoint, terminate the process, start a new process, query for the memory, and pass only if the intended record is recovered.

## PERSISTENCE-002 — dialogue continuity

Record a turn, restart, request recent dialogue, verify timestamp/order/content.

## WEIGHT-001 — adaptive persistence

Update a named weight, restart, verify value and update count survive.

## STATE-001 — organism/application state

Persist a state key, restart, verify exact decoded value.

## USB-001 — portable restore

Initialize portable memory, write memory, snapshot, safely close, reopen from a second process/path, recall.

## USB-002 — integrity failure

Modify a tracked file after generating `integrity.json`; verification must fail.

## CRASH-001 — interrupted generation

Persist input event, simulate generator exception, verify input event still exists and no fabricated response turn is recorded.

## CONSOLIDATION-001 — source preservation

Create a derived lesson; confirm all primary source memories still exist and lesson stores their IDs.

## RETRIEVAL-001 — relevance

Build a frozen memory corpus and query set. Report Recall@K / MRR instead of anecdotes.

## SCALE-001 — large store

Measure write latency, recall latency, database size, and recovery time at 1k, 10k, 100k, and larger record counts appropriate to your target.

## CLAIM-001 — no semantic overclaim

If using the built-in feature-hash baseline, documentation must not call it a neural semantic embedding model.
