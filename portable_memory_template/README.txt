COSMIC RECONCILIATION PORTABLE MEMORY

Create a working drive with:
    cosmic-memory usb-init <PATH-TO-DRIVE>

The library creates:
    COSMIC_MEMORY/manifest.json
    COSMIC_MEMORY/integrity.json
    COSMIC_MEMORY/memory.db
    COSMIC_MEMORY/snapshots/
    COSMIC_MEMORY/exports/

The database is deliberately ordinary SQLite so the owner can inspect, copy,
backup, migrate, and recover it without a proprietary service.

IMPORTANT: default storage is not encrypted by this library. Use full-volume
or OS encryption for sensitive material. Never store API keys as memories.
