from __future__ import annotations

import argparse
import json
from pathlib import Path

from .consolidation import simple_recurrence_consolidation
from .store import MemoryStore
from .usb import (
    initialize_portable_memory,
    restore_snapshot,
    snapshot_portable_memory,
    sync_database,
    verify_portable_memory,
)


def _db(args: argparse.Namespace) -> Path:
    return Path(args.db).expanduser()


def _json_value(raw: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def main() -> None:
    parser = argparse.ArgumentParser(prog="cosmic-memory", description="Cosmic Reconciliation durable memory toolkit")
    parser.add_argument("--db", default="./cosmic_memory.db", help="Path to local memory database")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="Initialize a local memory database")

    p = sub.add_parser("remember", help="Store a durable memory")
    p.add_argument("content")
    p.add_argument("--tag", action="append", default=[])
    p.add_argument("--importance", type=float, default=0.5)

    p = sub.add_parser("recall", help="Recall memories")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=8)

    p = sub.add_parser("forget", help="Delete one durable semantic memory by ID")
    p.add_argument("memory_id")

    p = sub.add_parser("purge-session", help="Delete stored dialogue for a session")
    p.add_argument("session_id")
    p.add_argument("--hard-delete-events", action="store_true")

    sub.add_parser("stats", help="Show store counts")
    sub.add_parser("integrity", help="Run SQLite integrity checks")
    sub.add_parser("weights", help="Show adaptive/model-trust weights")

    p = sub.add_parser("state-get", help="Read a persistent application/organism state value")
    p.add_argument("key")

    p = sub.add_parser("state-set", help="Write a persistent application/organism state value")
    p.add_argument("key")
    p.add_argument("value", help="JSON value or plain string")

    p = sub.add_parser("consolidate", help="Create idempotent recurring-theme lessons")
    p.add_argument("--min-occurrences", type=int, default=3)
    p.add_argument("--max-lessons", type=int, default=6)

    p = sub.add_parser("usb-init", help="Create a portable memory on a USB/directory")
    p.add_argument("path")
    p.add_argument("--label", default="Cosmic Reconciliation Memory")

    p = sub.add_parser("usb-verify", help="Verify portable hashes and SQLite integrity")
    p.add_argument("path")

    p = sub.add_parser("usb-snapshot", help="Snapshot portable memory database")
    p.add_argument("path")
    p.add_argument("--name")

    p = sub.add_parser("usb-sync", help="Safely sync --db onto portable storage")
    p.add_argument("path")
    p.add_argument("--overwrite", action="store_true", help="Do not make a pre-sync snapshot")

    p = sub.add_parser("usb-restore", help="Restore a snapshot from portable storage")
    p.add_argument("path")
    p.add_argument("snapshot", help="Snapshot filename inside COSMIC_MEMORY/snapshots")
    p.add_argument("--no-backup-current", action="store_true")

    args = parser.parse_args()

    if args.cmd == "usb-init":
        print(initialize_portable_memory(args.path, args.label))
        return
    if args.cmd == "usb-verify":
        result = verify_portable_memory(args.path)
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result.get("ok") else 1)
    if args.cmd == "usb-snapshot":
        print(snapshot_portable_memory(args.path, args.name))
        return
    if args.cmd == "usb-sync":
        print(sync_database(_db(args), args.path, overwrite=args.overwrite))
        return
    if args.cmd == "usb-restore":
        print(restore_snapshot(args.path, args.snapshot, backup_current=not args.no_backup_current))
        return

    with MemoryStore(_db(args)) as store:
        if args.cmd == "init":
            print(_db(args))
        elif args.cmd == "remember":
            print(store.remember(args.content, args.tag, args.importance))
        elif args.cmd == "recall":
            print(json.dumps([{
                "memory_id": r.memory_id,
                "content": r.content,
                "score": r.score,
                "importance": r.importance,
                "tags": r.tags,
                "created_at": r.created_at,
                "metadata": r.metadata,
            } for r in store.recall(args.query, args.limit)], indent=2))
        elif args.cmd == "forget":
            deleted = store.forget(args.memory_id)
            print(json.dumps({"deleted": deleted, "memory_id": args.memory_id}))
            raise SystemExit(0 if deleted else 2)
        elif args.cmd == "purge-session":
            print(json.dumps(store.purge_session(args.session_id, hard_delete_events=args.hard_delete_events), indent=2))
        elif args.cmd == "stats":
            print(json.dumps(store.stats(), indent=2))
        elif args.cmd == "integrity":
            result = store.integrity_check()
            print(json.dumps(result, indent=2))
            raise SystemExit(0 if result.get("ok") else 1)
        elif args.cmd == "weights":
            print(json.dumps(store.weights(), indent=2))
        elif args.cmd == "state-get":
            print(json.dumps({"key": args.key, "value": store.get_state(args.key)}, indent=2))
        elif args.cmd == "state-set":
            store.set_state(args.key, _json_value(args.value))
            print(json.dumps({"key": args.key, "value": store.get_state(args.key)}, indent=2))
        elif args.cmd == "consolidate":
            created = simple_recurrence_consolidation(store, args.min_occurrences, args.max_lessons)
            print(json.dumps({"created_lesson_ids": created, "created": len(created)}, indent=2))


if __name__ == "__main__":
    main()
