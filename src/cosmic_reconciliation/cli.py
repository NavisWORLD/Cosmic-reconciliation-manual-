from __future__ import annotations

import argparse
import json
from pathlib import Path

from .store import MemoryStore
from .usb import initialize_portable_memory, snapshot_portable_memory, verify_portable_memory


def _db(args: argparse.Namespace) -> Path:
    return Path(args.db).expanduser()


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
    sub.add_parser("stats", help="Show store counts")
    p = sub.add_parser("usb-init", help="Create a portable memory on a USB/directory")
    p.add_argument("path")
    p = sub.add_parser("usb-verify", help="Verify portable memory hashes")
    p.add_argument("path")
    p = sub.add_parser("usb-snapshot", help="Snapshot portable memory database")
    p.add_argument("path")

    args = parser.parse_args()
    if args.cmd == "usb-init":
        print(initialize_portable_memory(args.path))
        return
    if args.cmd == "usb-verify":
        print(json.dumps(verify_portable_memory(args.path), indent=2))
        return
    if args.cmd == "usb-snapshot":
        print(snapshot_portable_memory(args.path))
        return

    with MemoryStore(_db(args)) as store:
        if args.cmd == "init":
            print(_db(args))
        elif args.cmd == "remember":
            print(store.remember(args.content, args.tag, args.importance))
        elif args.cmd == "recall":
            print(json.dumps([{
                "memory_id": r.memory_id, "content": r.content, "score": r.score,
                "importance": r.importance, "tags": r.tags, "created_at": r.created_at, "metadata": r.metadata
            } for r in store.recall(args.query, args.limit)], indent=2))
        elif args.cmd == "stats":
            print(json.dumps(store.stats(), indent=2))


if __name__ == "__main__":
    main()
