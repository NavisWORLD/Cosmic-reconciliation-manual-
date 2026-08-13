from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .store import MemoryStore
from .usb import (
    initialize_portable_memory,
    memory_root,
    snapshot_portable_memory,
    sync_database,
    verify_portable_memory,
)


class CosmicMemoryDesktop(tk.Tk):
    """Small native desktop control surface for Cosmic Reconciliation Memory."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Cosmic Reconciliation Memory")
        self.geometry("980x700")
        self.minsize(820, 600)
        self.store: MemoryStore | None = None
        self.db_var = tk.StringVar(value=str(Path.home() / "CosmicMemory" / "memory.db"))
        self.status_var = tk.StringVar(value="Ready")
        self._configure_style()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._open_store()

    def _configure_style(self) -> None:
        self.configure(bg="#0d1117")
        style = ttk.Style(self)
        for theme in ("clam", "alt", "default"):
            if theme in style.theme_names():
                style.theme_use(theme)
                break
        style.configure("TFrame", background="#0d1117")
        style.configure("Card.TFrame", background="#161b22")
        style.configure("TLabel", background="#0d1117", foreground="#e6edf3", font=("Segoe UI", 10))
        style.configure("Title.TLabel", background="#0d1117", foreground="#7ee787", font=("Segoe UI", 22, "bold"))
        style.configure("Muted.TLabel", background="#0d1117", foreground="#8b949e")
        style.configure("TButton", padding=(10, 7))
        style.configure("Accent.TButton", padding=(12, 8), font=("Segoe UI", 10, "bold"))
        style.configure("TNotebook", background="#0d1117", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(16, 9))

    def _build_ui(self) -> None:
        shell = ttk.Frame(self, padding=18)
        shell.pack(fill="both", expand=True)

        ttk.Label(shell, text="COSMIC MEMORY", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            shell,
            text="Local-first durable memory • portable snapshots • owner-controlled recall",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(0, 14))

        top = ttk.Frame(shell)
        top.pack(fill="x", pady=(0, 10))
        ttk.Label(top, text="Database").pack(side="left")
        ttk.Entry(top, textvariable=self.db_var).pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(top, text="Browse", command=self._browse_db).pack(side="left", padx=(0, 6))
        ttk.Button(top, text="Open", style="Accent.TButton", command=self._open_store).pack(side="left")

        self.tabs = ttk.Notebook(shell)
        self.tabs.pack(fill="both", expand=True)
        self._build_recall_tab()
        self._build_remember_tab()
        self._build_portable_tab()
        self._build_status_tab()

        status = ttk.Frame(shell)
        status.pack(fill="x", pady=(10, 0))
        ttk.Label(status, textvariable=self.status_var, style="Muted.TLabel").pack(side="left")

    def _build_recall_tab(self) -> None:
        tab = ttk.Frame(self.tabs, padding=16)
        self.tabs.add(tab, text="Recall")
        bar = ttk.Frame(tab)
        bar.pack(fill="x")
        self.query_var = tk.StringVar()
        entry = ttk.Entry(bar, textvariable=self.query_var)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda _e: self._recall())
        ttk.Button(bar, text="Search memory", style="Accent.TButton", command=self._recall).pack(side="left", padx=(8, 0))
        self.recall_text = tk.Text(tab, wrap="word", bg="#161b22", fg="#e6edf3", insertbackground="#e6edf3", relief="flat", padx=14, pady=14)
        self.recall_text.pack(fill="both", expand=True, pady=(12, 0))

    def _build_remember_tab(self) -> None:
        tab = ttk.Frame(self.tabs, padding=16)
        self.tabs.add(tab, text="Remember")
        ttk.Label(tab, text="Memory content").pack(anchor="w")
        self.memory_text = tk.Text(tab, height=12, wrap="word", bg="#161b22", fg="#e6edf3", insertbackground="#e6edf3", relief="flat", padx=14, pady=14)
        self.memory_text.pack(fill="both", expand=True, pady=(6, 12))
        form = ttk.Frame(tab)
        form.pack(fill="x")
        ttk.Label(form, text="Tags (comma separated)").grid(row=0, column=0, sticky="w")
        self.tags_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.tags_var).grid(row=1, column=0, sticky="ew", padx=(0, 12))
        ttk.Label(form, text="Importance 0–1").grid(row=0, column=1, sticky="w")
        self.importance_var = tk.StringVar(value="0.7")
        ttk.Entry(form, textvariable=self.importance_var, width=12).grid(row=1, column=1, sticky="w")
        ttk.Button(form, text="Store memory", style="Accent.TButton", command=self._remember).grid(row=1, column=2, padx=(12, 0))
        form.columnconfigure(0, weight=1)

    def _build_portable_tab(self) -> None:
        tab = ttk.Frame(self.tabs, padding=16)
        self.tabs.add(tab, text="Portable drive")
        ttk.Label(tab, text="USB / external drive / test directory").pack(anchor="w")
        row = ttk.Frame(tab)
        row.pack(fill="x", pady=(6, 12))
        self.portable_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.portable_var).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Browse", command=self._browse_portable).pack(side="left", padx=(8, 0))

        buttons = ttk.Frame(tab)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Initialize", command=self._usb_init).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Sync current DB", command=self._usb_sync).pack(side="left", padx=6)
        ttk.Button(buttons, text="Snapshot", command=self._usb_snapshot).pack(side="left", padx=6)
        ttk.Button(buttons, text="Verify", style="Accent.TButton", command=self._usb_verify).pack(side="left", padx=6)

        self.portable_text = tk.Text(tab, wrap="word", bg="#161b22", fg="#e6edf3", insertbackground="#e6edf3", relief="flat", padx=14, pady=14)
        self.portable_text.pack(fill="both", expand=True, pady=(14, 0))
        self.portable_text.insert("end", "Portable memory keeps memory.db, manifests, integrity hashes, and snapshots together.\n")

    def _build_status_tab(self) -> None:
        tab = ttk.Frame(self.tabs, padding=16)
        self.tabs.add(tab, text="Health")
        row = ttk.Frame(tab)
        row.pack(fill="x")
        ttk.Button(row, text="Refresh", style="Accent.TButton", command=self._refresh_status).pack(side="left")
        ttk.Button(row, text="Checkpoint", command=self._checkpoint).pack(side="left", padx=8)
        self.health_text = tk.Text(tab, wrap="word", bg="#161b22", fg="#e6edf3", insertbackground="#e6edf3", relief="flat", padx=14, pady=14)
        self.health_text.pack(fill="both", expand=True, pady=(12, 0))

    def _browse_db(self) -> None:
        chosen = filedialog.asksaveasfilename(title="Choose memory database", defaultextension=".db", filetypes=[("SQLite database", "*.db"), ("All files", "*")])
        if chosen:
            self.db_var.set(chosen)

    def _browse_portable(self) -> None:
        chosen = filedialog.askdirectory(title="Choose portable drive or directory")
        if chosen:
            self.portable_var.set(chosen)

    def _open_store(self) -> None:
        try:
            if self.store:
                self.store.close()
            self.store = MemoryStore(Path(self.db_var.get()).expanduser())
            self.status_var.set(f"Opened {self.store.path}")
            self._refresh_status()
        except Exception as exc:
            messagebox.showerror("Open failed", str(exc))

    def _need_store(self) -> MemoryStore:
        if self.store is None:
            raise RuntimeError("Open a memory database first")
        return self.store

    def _recall(self) -> None:
        try:
            results = self._need_store().recall(self.query_var.get(), limit=20)
            self.recall_text.delete("1.0", "end")
            if not results:
                self.recall_text.insert("end", "No matching memories.\n")
            for item in results:
                self.recall_text.insert("end", f"{item.score:.3f}  •  importance {item.importance:.2f}\n{item.content}\nTags: {', '.join(item.tags)}\nID: {item.memory_id}\n\n")
            self.status_var.set(f"Recalled {len(results)} memories")
        except Exception as exc:
            messagebox.showerror("Recall failed", str(exc))

    def _remember(self) -> None:
        try:
            text = self.memory_text.get("1.0", "end").strip()
            if not text:
                return
            tags = [t.strip() for t in self.tags_var.get().split(",") if t.strip()]
            importance = float(self.importance_var.get())
            memory_id = self._need_store().remember(text, tags=tags, importance=importance)
            self.memory_text.delete("1.0", "end")
            self.status_var.set(f"Stored {memory_id}")
            messagebox.showinfo("Stored", "Memory saved durably.")
        except Exception as exc:
            messagebox.showerror("Store failed", str(exc))

    def _portable_path(self) -> str:
        path = self.portable_var.get().strip()
        if not path:
            raise ValueError("Choose a portable drive or directory")
        return path

    def _usb_init(self) -> None:
        try:
            root = initialize_portable_memory(self._portable_path())
            self._portable_log({"initialized": str(root)})
        except Exception as exc:
            messagebox.showerror("Portable init failed", str(exc))

    def _usb_sync(self) -> None:
        try:
            store = self._need_store()
            store.checkpoint()
            out = sync_database(store.path, self._portable_path(), overwrite=False)
            self._portable_log({"synced": str(out)})
        except Exception as exc:
            messagebox.showerror("Portable sync failed", str(exc))

    def _usb_snapshot(self) -> None:
        try:
            out = snapshot_portable_memory(self._portable_path())
            self._portable_log({"snapshot": str(out)})
        except Exception as exc:
            messagebox.showerror("Snapshot failed", str(exc))

    def _usb_verify(self) -> None:
        try:
            result = verify_portable_memory(self._portable_path())
            self._portable_log(result)
            if result.get("ok"):
                messagebox.showinfo("Verified", "Portable memory integrity checks passed.")
            else:
                messagebox.showwarning("Verification failed", json.dumps(result, indent=2))
        except Exception as exc:
            messagebox.showerror("Verification failed", str(exc))

    def _portable_log(self, value: object) -> None:
        self.portable_text.delete("1.0", "end")
        self.portable_text.insert("end", json.dumps(value, indent=2, default=str))

    def _refresh_status(self) -> None:
        try:
            store = self._need_store()
            payload = {
                "database": str(store.path),
                "counts": store.stats(),
                "integrity": store.integrity_check(),
                "weights": store.weights(),
            }
            self.health_text.delete("1.0", "end")
            self.health_text.insert("end", json.dumps(payload, indent=2, default=str))
        except Exception as exc:
            self.health_text.delete("1.0", "end")
            self.health_text.insert("end", f"Health check failed: {exc}")

    def _checkpoint(self) -> None:
        try:
            self._need_store().checkpoint()
            self.status_var.set("Checkpoint complete")
        except Exception as exc:
            messagebox.showerror("Checkpoint failed", str(exc))

    def _on_close(self) -> None:
        try:
            if self.store:
                self.store.close()
        finally:
            self.destroy()


def main() -> None:
    CosmicMemoryDesktop().mainloop()


if __name__ == "__main__":
    main()
