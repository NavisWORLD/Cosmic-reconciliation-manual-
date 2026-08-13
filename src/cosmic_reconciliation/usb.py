from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from .models import utc_now
from .store import MemoryStore

ROOT_NAME = "COSMIC_MEMORY"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def memory_root(drive_or_dir: str | os.PathLike[str]) -> Path:
    p = Path(drive_or_dir).expanduser().resolve()
    return p if p.name == ROOT_NAME else p / ROOT_NAME


def initialize_portable_memory(
    drive_or_dir: str | os.PathLike[str],
    label: str = "Cosmic Reconciliation Memory",
) -> Path:
    root = memory_root(drive_or_dir)
    (root / "snapshots").mkdir(parents=True, exist_ok=True)
    (root / "exports").mkdir(parents=True, exist_ok=True)
    manifest = {
        "format": "cosmic-reconciliation-portable-memory",
        "version": 1,
        "label": label,
        "created_at": utc_now(),
        "security": {
            "encrypted_by_library": False,
            "note": "Use OS/full-volume encryption for sensitive memories. Never place API keys in memory records.",
        },
        "database": "memory.db",
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    with MemoryStore(root / "memory.db") as store:
        store.set_state("portable_memory", {"label": label, "created_at": manifest["created_at"]})
        store.checkpoint()
    write_integrity_manifest(root)
    return root


def write_integrity_manifest(root: str | os.PathLike[str]) -> Path:
    root = Path(root)
    files: dict[str, dict[str, Any]] = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.name == "integrity.json":
            continue
        rel = p.relative_to(root).as_posix()
        files[rel] = {"sha256": sha256_file(p), "bytes": p.stat().st_size}
    out = root / "integrity.json"
    out.write_text(json.dumps({"generated_at": utc_now(), "files": files}, indent=2), encoding="utf-8")
    return out


def _sqlite_integrity(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"ok": False, "messages": ["database missing"]}
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=30.0)
    try:
        rows = [str(r[0]) for r in conn.execute("PRAGMA integrity_check").fetchall()]
    finally:
        conn.close()
    return {"ok": rows == ["ok"], "messages": rows}


def verify_portable_memory(drive_or_dir: str | os.PathLike[str]) -> dict[str, Any]:
    root = memory_root(drive_or_dir)
    manifest_path = root / "manifest.json"
    integrity = root / "integrity.json"
    failures: list[dict[str, str]] = []

    if not manifest_path.exists():
        failures.append({"path": "manifest.json", "error": "missing"})
        manifest: dict[str, Any] = {}
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            manifest = {}
            failures.append({"path": "manifest.json", "error": "invalid_json"})

    if manifest and manifest.get("format") != "cosmic-reconciliation-portable-memory":
        failures.append({"path": "manifest.json", "error": "wrong_format"})

    if not integrity.exists():
        return {
            "ok": False,
            "root": str(root),
            "failures": failures + [{"path": "integrity.json", "error": "missing"}],
            "checked": 0,
            "database": _sqlite_integrity(root / "memory.db"),
        }

    try:
        data = json.loads(integrity.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "ok": False,
            "root": str(root),
            "failures": failures + [{"path": "integrity.json", "error": "invalid_json"}],
            "checked": 0,
            "database": _sqlite_integrity(root / "memory.db"),
        }

    for rel, expected in data.get("files", {}).items():
        p = root / rel
        if not p.exists():
            failures.append({"path": rel, "error": "missing"})
            continue
        actual = sha256_file(p)
        if actual != expected.get("sha256"):
            failures.append({"path": rel, "error": "hash_mismatch", "actual": actual})
        elif int(expected.get("bytes", -1)) != p.stat().st_size:
            failures.append({"path": rel, "error": "size_mismatch"})

    db_status = _sqlite_integrity(root / "memory.db")
    if not db_status["ok"]:
        failures.append({"path": "memory.db", "error": "sqlite_integrity_failed"})
    return {
        "ok": not failures,
        "root": str(root),
        "failures": failures,
        "checked": len(data.get("files", {})),
        "database": db_status,
    }


def snapshot_portable_memory(drive_or_dir: str | os.PathLike[str], name: str | None = None) -> Path:
    root = memory_root(drive_or_dir)
    db = root / "memory.db"
    if not db.exists():
        raise FileNotFoundError(f"No portable memory database at {db}")
    safe_name = name or utc_now().replace(":", "-")
    target = root / "snapshots" / f"{safe_name}.db"
    with MemoryStore(db) as store:
        store.backup_to(target)
    write_integrity_manifest(root)
    return target


def sync_database(
    source_db: str | os.PathLike[str],
    drive_or_dir: str | os.PathLike[str],
    overwrite: bool = False,
) -> Path:
    """Copy a SQLite memory store onto portable storage safely.

    When an existing portable database is present and ``overwrite`` is false,
    a pre-sync snapshot is made first. The actual copy uses SQLite's backup API
    so committed WAL-resident state is included.
    """
    root = memory_root(drive_or_dir)
    if not root.exists():
        initialize_portable_memory(drive_or_dir)
    src = Path(source_db).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(src)
    dst = root / "memory.db"
    if dst.exists() and not overwrite:
        snapshot_portable_memory(root, "pre-sync")
    with MemoryStore(src) as source:
        source.backup_to(dst)
    write_integrity_manifest(root)
    return dst


def restore_snapshot(
    drive_or_dir: str | os.PathLike[str],
    snapshot: str | os.PathLike[str],
    *,
    backup_current: bool = True,
) -> Path:
    """Restore a named/path snapshot into the active portable database."""
    root = memory_root(drive_or_dir)
    snap = Path(snapshot)
    if not snap.is_absolute():
        snap = root / "snapshots" / snap
    snap = snap.expanduser().resolve()
    snapshots_root = (root / "snapshots").resolve()
    if snapshots_root not in snap.parents:
        raise ValueError("snapshot must be inside the portable snapshots directory")
    if not snap.exists():
        raise FileNotFoundError(snap)
    if not _sqlite_integrity(snap)["ok"]:
        raise ValueError(f"snapshot failed SQLite integrity check: {snap}")

    dst = root / "memory.db"
    if dst.exists() and backup_current:
        snapshot_portable_memory(root, "pre-restore")

    source = sqlite3.connect(f"file:{snap}?mode=ro", uri=True, timeout=30.0)
    target = sqlite3.connect(dst, timeout=30.0)
    try:
        source.backup(target)
        target.commit()
    finally:
        target.close()
        source.close()
    write_integrity_manifest(root)
    return dst
