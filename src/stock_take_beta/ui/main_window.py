import tkinter as tk
from tkinter import ttk
from typing import Any

from ..config import APP_NAME, APP_SUBTITLE, COLORS
from ..services.progress_store import ProgressStore


class MainWindow(tk.Tk):
    def __init__(self, progress_store: ProgressStore) -> None:
        super().__init__()
        self.progress_store = progress_store
        self.state_data: dict[str, Any] = self.progress_store.load()

        self.title(f"{APP_NAME} — Massimo's Rail")
        self.geometry("1280x780")
        self.minsize(1020, 680)
        self.configure(bg=COLORS["cream"])

        self._configure_styles()
        self._build_layout()
        self.show_audit()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Stock.Treeview",
            background=COLORS["cream_light"],
            fieldbackground=COLORS["cream_light"],
            foreground=COLORS["text"],
            rowheight=34,
            borderwidth=0,
            font=("Arial", 10),
        )
        style.configure(
            "Stock.Treeview.Heading",
            background=COLORS["green"],
            foreground=COLORS["white"],
            relief="flat",
            font=("Arial", 10, "bold"),
        )
        style.map("Stock.Treeview", background=[("selected", COLORS["green_soft"])])

    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = tk.Frame(self, bg=COLORS["green"], width=238)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        brand = tk.Label(
            self.sidebar,
            text="MASSIMO'S\nRAIL",
            bg=COLORS["green"],
            fg=COLORS["cream_light"],
            font=("Arial", 20, "bold"),
            justify="left",
        )
        brand.pack(anchor="w", padx=28, pady=(30, 4))

        tk.Label(
            self.sidebar,
            text="STOCK TAKE BETA",
            bg=COLORS["green"],
            fg="#BFCFC5",
            font=("Arial", 9, "bold"),
        ).pack(anchor="w", padx=29, pady=(0, 32))

        self.audit_button = self._nav_button("Stock Audit", self.show_audit)
        self.audit_button.pack(fill="x", padx=16, pady=4)
        self.unlisted_button = self._nav_button("Unlisted Physical Stock", self.show_unlisted)
        self.unlisted_button.pack(fill="x", padx=16, pady=4)

        tk.Frame(self.sidebar, bg=COLORS["green_mid"], height=1).pack(
            fill="x", padx=20, pady=22
        )
        tk.Label(
            self.sidebar,
            text="Standalone audit tool\nNo marketplace writes",
            bg=COLORS["green"],
            fg="#BFCFC5",
            font=("Arial", 9),
            justify="left",
        ).pack(anchor="w", padx=28)

        self.content = tk.Frame(self, bg=COLORS["cream"])
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)

        self.header = tk.Frame(self.content, bg=COLORS["cream"])
        self.header.grid(row=0, column=0, sticky="ew", padx=34, pady=(28, 14))
        self.header.grid_columnconfigure(0, weight=1)

        self.page_title = tk.Label(
            self.header,
            text=APP_NAME,
            bg=COLORS["cream"],
            fg=COLORS["text"],
            font=("Arial", 25, "bold"),
        )
        self.page_title.grid(row=0, column=0, sticky="w")
        self.page_subtitle = tk.Label(
            self.header,
            text=APP_SUBTITLE,
            bg=COLORS["cream"],
            fg=COLORS["muted"],
            font=("Arial", 10),
        )
        self.page_subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.save_status = tk.Label(
            self.header,
            text="Progress saves locally",
            bg=COLORS["green_soft"],
            fg=COLORS["green"],
            font=("Arial", 9, "bold"),
            padx=12,
            pady=7,
        )
        self.save_status.grid(row=0, column=1, rowspan=2, sticky="e")

        self.body = tk.Frame(self.content, bg=COLORS["cream"])
        self.body.grid(row=1, column=0, sticky="nsew", padx=34, pady=(0, 30))
        self.body.grid_columnconfigure(0, weight=1)
        self.body.grid_rowconfigure(1, weight=1)

    def _nav_button(self, text: str, command) -> tk.Button:
        return tk.Button(
            self.sidebar,
            text=text,
            command=command,
            anchor="w",
            bg=COLORS["green"],
            fg=COLORS["cream_light"],
            activebackground=COLORS["green_mid"],
            activeforeground=COLORS["white"],
            bd=0,
            relief="flat",
            padx=12,
            pady=12,
            font=("Arial", 10, "bold"),
            cursor="hand2",
        )

    def _clear_body(self) -> None:
        for child in self.body.winfo_children():
            child.destroy()

    def _summary_card(self, parent: tk.Widget, title: str, value: str, column: int) -> None:
        card = tk.Frame(
            parent,
            bg=COLORS["cream_light"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 8, 8))
        parent.grid_columnconfigure(column, weight=1)
        tk.Label(
            card,
            text=title.upper(),
            bg=COLORS["cream_light"],
            fg=COLORS["muted"],
            font=("Arial", 8, "bold"),
        ).pack(anchor="w", padx=16, pady=(13, 2))
        tk.Label(
            card,
            text=value,
            bg=COLORS["cream_light"],
            fg=COLORS["green"],
            font=("Arial", 20, "bold"),
        ).pack(anchor="w", padx=16, pady=(0, 13))

    def show_audit(self) -> None:
        self._clear_body()
        self.page_title.config(text="Shorts Stock Audit")
        self.page_subtitle.config(
            text="Marketplace rows will be matched by SKU and shown in SKU order."
        )

        summaries = tk.Frame(self.body, bg=COLORS["cream"])
        summaries.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        self._summary_card(summaries, "Online SKUs", "—", 0)
        self._summary_card(summaries, "Physically checked", "0", 1)
        self._summary_card(summaries, "Missing", "—", 2)
        self._summary_card(summaries, "To check", "—", 3)

        panel = tk.Frame(
            self.body,
            bg=COLORS["cream_light"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        panel.grid(row=1, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        top = tk.Frame(panel, bg=COLORS["cream_light"])
        top.grid(row=0, column=0, sticky="ew", padx=18, pady=16)
        top.grid_columnconfigure(0, weight=1)
        tk.Label(
            top,
            text="Audit queue",
            bg=COLORS["cream_light"],
            fg=COLORS["text"],
            font=("Arial", 13, "bold"),
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            top,
            text="Marketplace data not connected yet",
            bg=COLORS["cream_light"],
            fg=COLORS["muted"],
            font=("Arial", 9),
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        columns = ("sku", "vinted", "etsy", "ebay", "physical")
        tree = ttk.Treeview(panel, columns=columns, show="headings", style="Stock.Treeview")
        tree.heading("sku", text="SKU")
        tree.heading("vinted", text="Vinted")
        tree.heading("etsy", text="Etsy")
        tree.heading("ebay", text="eBay")
        tree.heading("physical", text="Physical stock")
        tree.column("sku", width=145, anchor="w")
        tree.column("vinted", width=130, anchor="center")
        tree.column("etsy", width=130, anchor="center")
        tree.column("ebay", width=130, anchor="center")
        tree.column("physical", width=170, anchor="center")
        tree.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 8))

        empty = tk.Label(
            panel,
            text="The shell is ready. Marketplace import and SKU matching are the next phase.",
            bg=COLORS["cream_light"],
            fg=COLORS["muted"],
            font=("Arial", 10),
        )
        empty.grid(row=2, column=0, pady=(4, 18))

    def show_unlisted(self) -> None:
        self._clear_body()
        self.page_title.config(text="Unlisted Physical Stock")
        self.page_subtitle.config(
            text="Record shorts you physically find that are not represented in the online audit."
        )

        panel = tk.Frame(
            self.body,
            bg=COLORS["cream_light"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        panel.grid(row=0, column=0, sticky="nsew")
        self.body.grid_rowconfigure(0, weight=1)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)

        tk.Label(
            panel,
            text="Found something that isn't listed online?",
            bg=COLORS["cream_light"],
            fg=COLORS["text"],
            font=("Arial", 14, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 5))
        tk.Label(
            panel,
            text="This section is separated from the main audit so physical anomalies do not get lost.",
            bg=COLORS["cream_light"],
            fg=COLORS["muted"],
            font=("Arial", 9),
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 15))

        columns = ("sku", "notes")
        tree = ttk.Treeview(panel, columns=columns, show="headings", style="Stock.Treeview")
        tree.heading("sku", text="SKU / identifier")
        tree.heading("notes", text="Notes")
        tree.column("sku", width=220, anchor="w")
        tree.column("notes", width=650, anchor="w")
        tree.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 12))

        footer = tk.Frame(panel, bg=COLORS["cream_light"])
        footer.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
        tk.Label(
            footer,
            text="Entry controls will be added alongside the audit workflow in the next build.",
            bg=COLORS["cream_light"],
            fg=COLORS["muted"],
            font=("Arial", 9),
        ).pack(side="left")

    def _on_close(self) -> None:
        self.progress_store.save(self.state_data)
        self.destroy()
