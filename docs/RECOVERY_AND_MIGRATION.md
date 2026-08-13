# Recovery and Migration Runbook

## Recovery principle

A memory system is not proven durable because `save()` returned successfully. It is proven when a clean process can reopen the persisted state and recover the intended information with intact provenance.

## Before moving a portable memory

1. stop or quiesce writers;
2. run `cosmic-memory usb-verify <drive>`;
3. create a named snapshot;
4. safely eject the device;
5. reconnect it on the destination machine;
6. verify again before opening it.

## Safe local-to-portable sync

```bash
cosmic-memory --db ./memory.db usb-sync /path/to/drive
```

The v1.1 implementation uses SQLite's online backup API rather than copying the main `.db` file directly. This matters because WAL-mode databases may contain committed state outside the main file until checkpointing occurs.

If a portable database already exists, the default behavior creates `snapshots/pre-sync.db` before replacing the active portable database. `--overwrite` suppresses that safety snapshot.

## Create a known-good snapshot

```bash
cosmic-memory usb-snapshot /path/to/drive --name known-good
```

The resulting snapshot is a transaction-consistent SQLite database under `COSMIC_MEMORY/snapshots/` and is included in the SHA-256 integrity manifest.

## Restore

```bash
cosmic-memory usb-restore /path/to/drive known-good.db
```

Restore validates the snapshot with SQLite `PRAGMA integrity_check` first. By default it also creates a `pre-restore` snapshot of the currently active portable database.

## Verification

```bash
cosmic-memory usb-verify /path/to/drive
```

A successful report requires both:

- all tracked files matching the recorded SHA-256/size entries; and
- the active `memory.db` returning `ok` from SQLite integrity checking.

Do not silently ignore a failed verification result.

## Schema compatibility

The initial public schema is version `1`, recorded in the SQLite `meta` table and portable manifest. v1.1 adds behavior and indexes but does not require destructive data migration.

Future schema upgrades should follow this rule:

```text
backup → verify → migrate copy → test reopen/recall → replace active database
```

Never experiment on the only copy of a personal memory store.

## Moving between operating systems

The database and JSON files are platform-neutral. Store application secrets, absolute model paths, and device-specific configuration outside memory records whenever possible. A memory should describe durable context, not accidentally bind the user to one machine.

## Damaged drive procedure

1. stop writing immediately;
2. copy recoverable files to a different device before experimenting;
3. verify every available snapshot;
4. choose the newest snapshot that passes SQLite integrity checks;
5. restore to a fresh portable directory;
6. regenerate `integrity.json` only after the recovered database has been independently checked.

Do not regenerate checksums over known-corrupt data and then call the drive healthy.

## Backup policy

A removable drive by itself is not a backup. Minimum recommended layout:

```text
active memory
+ encrypted local backup
+ second offline/remote encrypted backup
```

Periodically test that a backup can actually be opened and recalled from a fresh process.
