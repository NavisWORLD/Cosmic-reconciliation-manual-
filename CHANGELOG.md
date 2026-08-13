# Changelog

## 1.2.0 - 2026-08-13

Cross-platform application and binary distribution release.

### Added

- native desktop memory manager GUI;
- `cosmic-memory-desktop` launcher;
- PyInstaller desktop packaging;
- one-click Windows Inno Setup installer;
- portable Windows single-file EXE;
- macOS `.app`, DMG, and zipped app packaging;
- polished offline-first Capacitor mobile companion for Android and iOS;
- installable Android APK build;
- unsigned iOS Simulator `.app` build;
- cross-platform distribution documentation;
- GitHub Actions distribution matrix that validates all platform builds on pull requests;
- automatic GitHub Release `v1.2.0` publishing after all platform jobs succeed on `main`.

### Distribution boundary

A physical-iPhone/TestFlight/App Store artifact requires Apple Developer signing credentials and provisioning. The public workflow produces a real iOS app build for the Simulator but intentionally does not embed private Apple signing material or bypass platform signing requirements.

## 1.1.0 - 2026-08-12

Completion-audit release.

### Added

- public `MemoryStore.get_memory()` and `list_memories()` APIs;
- explicit `forget()` and `purge_session()` owner-deletion controls;
- SQLite `integrity_check()` and transaction-safe `backup_to()` APIs;
- duplicate event-ID collision protection;
- idempotent evidence-linked recurrence consolidation;
- observable/testable heartbeat counters, `status()`, and `run_once()`;
- portable SQLite-safe sync, database integrity verification, and snapshot restore;
- CLI commands for forgetting, purge, integrity, weights, state, consolidation, USB sync, and USB restore;
- API reference and recovery/migration runbook;
- automated tests for lifecycle persistence, consolidation, heartbeat, and full portable recovery.

### Fixed

- portable sync no longer relies on copying an active WAL-mode `.db` file directly;
- repeated consolidation no longer emits the same derived lesson for an unchanged evidence set;
- event replay remains idempotent, while conflicting reuse of an event ID now fails loudly.

### Compatibility

The SQLite schema remains version 1. Existing v1.0 databases are opened in place; v1.1 adds indexes and behavior without destructive migration.

## 1.0.0 - 2026-08-12

Initial open-source release of Cosmic Reconciliation Memory with durable semantic/dialogue/event memory, adaptive weights, persistent state, reconciliation adapter, heartbeat, portable-memory tooling, manuals, teacher course, schemas, examples, and Python 3.10-3.12 CI.
