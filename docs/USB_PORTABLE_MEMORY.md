# Portable Memory Drive Manual

## Goal

Create a user-owned removable memory that can travel between compatible projects and machines.

## What gets stored

```text
COSMIC_MEMORY/
├── manifest.json       format and security metadata
├── integrity.json      SHA-256 checksums
├── memory.db           primary SQLite memory
├── snapshots/          point-in-time database copies
└── exports/            optional user exports
```

## Initialize

```bash
cosmic-memory usb-init <mounted-drive-path>
```

The command works with a normal directory, so test with `./portable_demo` first.

## Verify before use

```bash
cosmic-memory usb-verify <mounted-drive-path>
```

If verification fails, do not silently continue. Inspect the reported missing/hash-mismatch files and restore from a known-good snapshot or backup.

## Safely move between computers

1. stop applications writing to `memory.db`;
2. create a snapshot;
3. close the store;
4. use the operating system's safe-eject function;
5. mount on the next machine;
6. verify integrity;
7. open the database.

## Encryption

The reference library does not encrypt memory itself. For personal conversations, biometrics, or private project data, use encrypted removable storage provided by the operating system or a vetted encryption solution. Do not put API keys in this database.

## Backup strategy

A portable drive is not a backup unless another copy exists.

```text
working memory drive
+ local encrypted backup
+ second offline snapshot
```

## Interoperability

The database can be opened with standard SQLite tooling. `manifest.json` and `integrity.json` are ordinary JSON. That is intentional: no proprietary cloud service is required to recover the owner's memories.

## Future extension: paired drives

Projects may add a signed pairing record to `manifest.json` and require an application-level cryptographic identity before loading private memories. This repository does not pretend that a plain USB serial number is a secure identity primitive.
