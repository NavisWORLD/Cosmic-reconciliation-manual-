from __future__ import annotations

import hashlib
import json
import os
import shutil
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


def initialize_portable_memory(drive_or_dir: str | os.PathLike[str], label: str = "Cosmic Reconciliation Memory") -> Path:
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
            "note": "Use OS/full-volume encryption for sensitive memories. Never place API keys in memory records."
        },
        "database": "memory.db"
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


def verify_portable_memory(drive_or_dir: str | os.PathLike[str]) -> dict[str, Any]:
    root = memory_root(drive_or_dir)
    integrity = root / "integrity.json"
    if not integrity.exists():
        return {"ok": False, "error": "integrity.json missing", "root": str(root)}
    data = json.loads(integrity.read_text(encoding="utf-8"))
    failures = []
    for rel, expected in data.get("files", {}).items():
        p = root / rel
        if not p.exists():
            failures.append({"path": rel, "error": "missing"})
            continue
        actual = sha256_file(p)
        if actual != expected.get("sha256"):
            failures.append({"path": rel, "error": "hash_mismatch", "actual": actual})
    return {"ok": not failures, "root": str(root), "failures": failures, "checked": len(data.get("files", {}))}


def snapshot_portable_memory(drive_or_dir: str | os.PathLike[str], name: str | None = None) -> Path:
    root = memory_root(drive_or_dir)
    db = root / "memory.db"
    if not db.exists():
        raise FileNotFoundError(f"No portable memory database at {db}")
    with MemoryStore(db) as store:
        store.checkpoint()
    safe_name = name or utc_now().replace(":", "-")
    target = root / "snapshots" / f"{safe_name}.db"
    shutil.copy2(db, target)
    write_integrity_manifest(root)
    return target


def sync_database(source_db: str | os.PathLike[str], drive_or_dir: str | os.PathLike[str], overwrite: bool = False) -> Path:
    root = memory_root(drive_or_dir)
    if not root.exists():
        initialize_portable_memory(drive_or_dir)
    src = Path(source_db).expanduser().resolve()
    dst = root / "memory.db"
    if dst.exists() and not overwrite:
        snapshot_portable_memory(root, "pre-sync")
    shutil.copy2(src, dst)
    write_integrity_manifest(root)
    return dst
