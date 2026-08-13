# Portable Memory Drive Manual

## Goal

Create a user-owned removable memory that can travel between compatible projects and machines.

## What gets stored

```text
COSMIC_MEMORY/
├── manifest.json       format and security metadata
├── integrity.json      SHA-256 checksums and byte sizes
├── memory.db           primary SQLite memory
├── snapshots/          point-in-time transaction-safe database copies
└── exports/            optional user exports
```

## Initialize

```bash
cosmic-memory usb-init <mounted-drive-path>
```

The command works with a normal directory, so test with `./portable_demo` first.

## Put an existing memory database on the drive

```bash
cosmic-memory --db ./memory.db usb-sync <mounted-drive-path>
```

v1.1 uses SQLite's backup API rather than a blind filesystem copy. This is important for WAL-mode databases because committed changes may still live in the WAL file. If a portable database already exists, a `pre-sync` snapshot is created first unless `--overwrite` is supplied.

## Verify before use

```bash
cosmic-memory usb-verify <mounted-drive-path>
```

Verification checks:

1. `manifest.json` exists, parses, and declares the expected portable format;
2. each tracked file matches its SHA-256 digest and recorded byte size;
3. `memory.db` passes SQLite `PRAGMA integrity_check`.

If verification fails, do not silently continue. Inspect the reported issue and recover from a known-good snapshot or backup.

## Create a snapshot

```bash
cosmic-memory usb-snapshot <mounted-drive-path> --name known-good
```

The snapshot is produced with SQLite's online backup mechanism and written under `COSMIC_MEMORY/snapshots/`.

## Restore a snapshot

```bash
cosmic-memory usb-restore <mounted-drive-path> known-good.db
```

Before restore, the selected snapshot must pass SQLite integrity checking. By default the currently active database is saved as a `pre-restore` snapshot before replacement.

## Safely move between computers

1. stop applications writing to `memory.db`;
2. verify the drive;
3. create a snapshot;
4. close the store;
5. use the operating system's safe-eject function;
6. mount on the next machine;
7. verify integrity again;
8. open the database.

## Encryption

The reference library does not encrypt memory itself. For personal conversations, biometrics, private project data, or relationship memory, use encrypted removable storage provided by the operating system or a vetted encryption solution. Do not put API keys in this database.

## Owner-controlled forgetting

A portable drive is not forced immortality. The owner can remove a semantic memory by ID:

```bash
cosmic-memory --db <path-to-memory.db> forget <memory-id>
```

Dialogue can be removed per session. Raw event records are preserved by default for provenance and removed only when the owner explicitly requests `--hard-delete-events`.

## Backup strategy

A portable drive is not a backup unless another copy exists.

```text
working memory drive
+ local encrypted backup
+ second offline or encrypted remote snapshot
```

Periodically prove that a snapshot can be reopened and recalled from a fresh process.

## Interoperability

The database can be opened with standard SQLite tooling. `manifest.json` and `integrity.json` are ordinary JSON. That is intentional: no proprietary cloud service is required to recover the owner's memories.

## Future extension: paired drives

Projects may add a signed pairing record to `manifest.json` and require an application-level cryptographic identity before loading private memories. This repository does not pretend that a plain USB serial number is a secure identity primitive.

See [RECOVERY_AND_MIGRATION.md](RECOVERY_AND_MIGRATION.md) for the failure/recovery runbook.
