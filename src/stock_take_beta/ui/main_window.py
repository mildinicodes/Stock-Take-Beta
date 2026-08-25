from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk

from ..config import APP_NAME, APP_SUBTITLE, COLORS
from ..services.audit_service import AuditService
from ..services.progress_store import ProgressStore


class MainWindow(tk.Tk):
    def __init__(self, progress_store: ProgressStore, audit_service: AuditService, mobile_url: str) -> None:
        super().__init__()
        self.progress_store = progress_store
        self.audit_service = audit_service
        self.mobile_url = mobile_url
        self.title(f"{APP_NAME} — Massimo's Rail")
        self.geometry("1320x800")
        self.minsize(1060, 700)
        self.configure(bg=COLORS["cream"])
        self._configure_styles()
        self._build_layout()
        self.show_audit()

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Stock.Treeview", background=COLORS["cream_light"], fieldbackground=COLORS["cream_light"], foreground=COLORS["text"], rowheight=34, borderwidth=0, font=("Arial", 10))
        style.configure("Stock.Treeview.Heading", background=COLORS["green"], foreground=COLORS["white"], relief="flat", font=("Arial", 10, "bold"))
        style.map("Stock.Treeview", background=[("selected", COLORS["green_soft"])])

    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        sidebar = tk.Frame(self, bg=COLORS["green"], width=238)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        tk.Label(sidebar, text="MASSIMO'S\nRAIL", bg=COLORS["green"], fg=COLORS["cream_light"], font=("Arial", 20, "bold"), justify="left").pack(anchor="w", padx=28, pady=(30, 4))
        tk.Label(sidebar, text="STOCK TAKE BETA", bg=COLORS["green"], fg="#BFCFC5", font=("Arial", 9, "bold")).pack(anchor="w", padx=29, pady=(0, 28))
        self._nav(sidebar, "Stock Audit", self.show_audit).pack(fill="x", padx=16, pady=4)
        self._nav(sidebar, "Unlisted Physical Stock", self.show_unlisted).pack(fill="x", padx=16, pady=4)
        tk.Frame(sidebar, bg=COLORS["green_mid"], height=1).pack(fill="x", padx=20, pady=20)
        tk.Label(sidebar, text="PHONE VIEW", bg=COLORS["green"], fg="#BFCFC5", font=("Arial", 8, "bold")).pack(anchor="w", padx=28)
        tk.Label(sidebar, text=self.mobile_url, bg=COLORS["green"], fg=COLORS["cream_light"], font=("Arial", 9), wraplength=180, justify="left").pack(anchor="w", padx=28, pady=(5, 0))
        tk.Label(sidebar, text="Open this address on your phone while both devices are on the same Wi-Fi.", bg=COLORS["green"], fg="#BFCFC5", font=("Arial", 8), wraplength=180, justify="left").pack(anchor="w", padx=28, pady=(7, 0))

        self.content = tk.Frame(self, bg=COLORS["cream"])
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)
        header = tk.Frame(self.content, bg=COLORS["cream"])
        header.grid(row=0, column=0, sticky="ew", padx=34, pady=(28, 14))
        header.grid_columnconfigure(0, weight=1)
        self.page_title = tk.Label(header, bg=COLORS["cream"], fg=COLORS["text"], font=("Arial", 25, "bold"))
        self.page_title.grid(row=0, column=0, sticky="w")
        self.page_subtitle = tk.Label(header, bg=COLORS["cream"], fg=COLORS["muted"], font=("Arial", 10))
        self.page_subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.status_label = tk.Label(header, text="Ready", bg=COLORS["green_soft"], fg=COLORS["green"], font=("Arial", 9, "bold"), padx=12, pady=7)
        self.status_label.grid(row=0, column=1, rowspan=2, sticky="e")
        self.body = tk.Frame(self.content, bg=COLORS["cream"])
        self.body.grid(row=1, column=0, sticky="nsew", padx=34, pady=(0, 30))
        self.body.grid_columnconfigure(0, weight=1)
        self.body.grid_rowconfigure(1, weight=1)

    def _nav(self, parent: tk.Widget, text: str, command) -> tk.Button:
        return tk.Button(parent, text=text, command=command, anchor="w", bg=COLORS["green"], fg=COLORS["cream_light"], activebackground=COLORS["green_mid"], activeforeground=COLORS["white"], bd=0, padx=12, pady=12, font=("Arial", 10, "bold"), cursor="hand2")

    def _clear(self) -> None:
        for child in self.body.winfo_children():
            child.destroy()

    def _button(self, parent: tk.Widget, text: str, command, secondary: bool = False) -> tk.Button:
        return tk.Button(parent, text=text, command=command, bg=COLORS["cream_light"] if secondary else COLORS["green"], fg=COLORS["green"] if secondary else COLORS["white"], activebackground=COLORS["green_mid"], activeforeground=COLORS["white"], bd=1 if secondary else 0, relief="solid" if secondary else "flat", padx=14, pady=9, font=("Arial", 9, "bold"), cursor="hand2")

    def _summary(self, parent: tk.Widget, title: str, value: str, col: int) -> None:
        card = tk.Frame(parent, bg=COLORS["cream_light"], highlightbackground=COLORS["border"], highlightthickness=1)
        card.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 8, 0))
        parent.grid_columnconfigure(col, weight=1)
        tk.Label(card, text=title.upper(), bg=COLORS["cream_light"], fg=COLORS["muted"], font=("Arial", 8, "bold")).pack(anchor="w", padx=14, pady=(11, 2))
        tk.Label(card, text=value, bg=COLORS["cream_light"], fg=COLORS["green"], font=("Arial", 19, "bold")).pack(anchor="w", padx=14, pady=(0, 11))

    def show_audit(self) -> None:
        self._clear()
        state = self.progress_store.load()
        items = state.get("marketplace_items", [])
        audit = state.get("audit", {})
        valid_ids = {item.get("audit_id") or item.get("sku") for item in items}
        found = sum(1 for key, value in audit.items() if key in valid_ids and value == "found")
        missing = sum(1 for key, value in audit.items() if key in valid_ids and value == "missing")
        unchecked = max(0, len(items) - found - missing)
        self.page_title.config(text="Shorts Stock Audit")
        refreshed = state.get("last_refreshed_at") or "Never"
        counts = state.get("marketplace_counts", {})
        count_text = " · ".join(
            f"{name.title()} {counts.get(name, 0)}" for name in ("vinted", "ebay", "etsy") if counts
        )
        subtitle = f"Crosslist Import · {count_text} · Last refresh: {refreshed}" if count_text else f"Crosslist Import · Vinted + eBay + Etsy · Last refresh: {refreshed}"
        self.page_subtitle.config(text=subtitle)

        summary = tk.Frame(self.body, bg=COLORS["cream"])
        summary.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self._summary(summary, "Audit Rows", str(len(items)), 0)
        self._summary(summary, "Found", str(found), 1)
        self._summary(summary, "Missing", str(missing), 2)
        self._summary(summary, "To check", str(unchecked), 3)

        panel = tk.Frame(self.body, bg=COLORS["cream_light"], highlightbackground=COLORS["border"], highlightthickness=1)
        panel.grid(row=1, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)
        toolbar = tk.Frame(panel, bg=COLORS["cream_light"])
        toolbar.grid(row=0, column=0, sticky="ew", padx=16, pady=14)
        self._button(toolbar, "Refresh Marketplace Data", self._refresh_marketplaces).pack(side="left")
        self._button(toolbar, "Mark Found", lambda: self._mark_selected("found"), secondary=True).pack(side="left", padx=(8, 0))
        self._button(toolbar, "Mark Missing", lambda: self._mark_selected("missing"), secondary=True).pack(side="left", padx=(8, 0))
        self._button(toolbar, "Complete Audit", self._complete_audit).pack(side="right")

        columns = ("sku", "vinted", "ebay", "etsy", "physical", "flags")
        self.tree = ttk.Treeview(panel, columns=columns, show="headings", style="Stock.Treeview")
        for key, title in (("sku", "SKU"), ("vinted", "Vinted"), ("ebay", "eBay"), ("etsy", "Etsy"), ("physical", "Physical"), ("flags", "Flags")):
            self.tree.heading(key, text=title)
        self.tree.column("sku", width=150, anchor="w")
        self.tree.column("vinted", width=100, anchor="center")
        self.tree.column("ebay", width=100, anchor="center")
        self.tree.column("etsy", width=100, anchor="center")
        self.tree.column("physical", width=120, anchor="center")
        self.tree.column("flags", width=240, anchor="w")
        self.tree.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 8))
        scrollbar = ttk.Scrollbar(panel, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=1, column=1, sticky="ns", pady=(0, 8))

        for item in items:
            markets = item.get("marketplaces", {})
            flags = [m.title() + " duplicate" for m, rows in markets.items() if len(rows) > 1]
            if item.get("non_unique_sku"):
                flags.insert(0, "Non-unique SKU")
            audit_id = item.get("audit_id") or item["sku"]
            status = audit.get(audit_id, "Unchecked").title()
            self.tree.insert("", "end", iid=audit_id, values=(
                item["sku"],
                "✓" if markets.get("vinted") else "—",
                "✓" if markets.get("ebay") else "—",
                "✓" if markets.get("etsy") else "—",
                status,
                ", ".join(flags),
            ))

        non_unique_count = sum(1 for item in items if item.get("non_unique_sku"))
        issues = tk.Label(panel, text=f"Missing SKU listings: {len(state.get('missing_sku', []))}   ·   Duplicate flags: {len(state.get('duplicates', []))}   ·   Non-unique SKU rows: {non_unique_count}", bg=COLORS["cream_light"], fg=COLORS["muted"], font=("Arial", 9))
        issues.grid(row=2, column=0, sticky="w", padx=16, pady=(2, 14))

    def _refresh_marketplaces(self) -> None:
        self.status_label.config(text="Refreshing Crosslist…")
        def worker() -> None:
            try:
                self.audit_service.refresh_marketplaces()
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("Crosslist refresh failed", str(exc)))
                self.after(0, lambda: self.status_label.config(text="Refresh failed"))
                return
            self.after(0, lambda: self.status_label.config(text="Refresh complete"))
            self.after(0, self.show_audit)
        threading.Thread(target=worker, daemon=True).start()

    def _mark_selected(self, status: str) -> None:
        selected = self.tree.selection() if hasattr(self, "tree") else ()
        if not selected:
            return
        for audit_id in selected:
            self.audit_service.set_physical_status(audit_id, status)
        self.show_audit()

    def _complete_audit(self) -> None:
        state = self.audit_service.complete_audit()
        summary = state.get("completion_summary", {})
        messagebox.showinfo("Audit complete", f"Found: {summary.get('found', 0)}\nMissing: {summary.get('missing', 0)}\nUnchecked: {summary.get('unchecked', 0)}\nUnlisted physical: {summary.get('unlisted_physical', 0)}")
        self.show_audit()

    def show_unlisted(self) -> None:
        self._clear()
        self.page_title.config(text="Unlisted Physical Stock")
        self.page_subtitle.config(text="Physical shorts found during stock take that are not represented online.")
        panel = tk.Frame(self.body, bg=COLORS["cream_light"], highlightbackground=COLORS["border"], highlightthickness=1)
        panel.grid(row=0, column=0, sticky="nsew")
        self.body.grid_rowconfigure(0, weight=1)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)
        entrybar = tk.Frame(panel, bg=COLORS["cream_light"])
        entrybar.grid(row=0, column=0, sticky="ew", padx=18, pady=16)
        self.unlisted_entry = tk.Entry(entrybar, font=("Arial", 12), width=24)
        self.unlisted_entry.pack(side="left")
        self._button(entrybar, "Add SKU", self._add_unlisted).pack(side="left", padx=8)
        self._button(entrybar, "Remove Selected", self._remove_unlisted, secondary=True).pack(side="left")
        self.unlisted_tree = ttk.Treeview(panel, columns=("sku",), show="headings", style="Stock.Treeview")
        self.unlisted_tree.heading("sku", text="SKU")
        self.unlisted_tree.column("sku", width=300, anchor="w")
        self.unlisted_tree.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))
        for sku in self.progress_store.load().get("unlisted_physical_stock", []):
            self.unlisted_tree.insert("", "end", iid=sku, values=(sku,))

    def _add_unlisted(self) -> None:
        sku = self.unlisted_entry.get().strip()
        if sku:
            self.audit_service.add_unlisted_sku(sku)
            self.show_unlisted()

    def _remove_unlisted(self) -> None:
        for sku in self.unlisted_tree.selection():
            self.audit_service.remove_unlisted_sku(sku)
        self.show_unlisted()
