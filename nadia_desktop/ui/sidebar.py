"""Left sidebar — discussions + New Discussion (maquette Desk)."""

from __future__ import annotations

import tkinter as tk
from typing import Callable

from ui import theme as T


class DeskSidebar(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        product: str,
        on_new: Callable[[], None],
        on_select: Callable[[int], None],
        discussions: list[str],
        active_index: int = 0,
        **kwargs,
    ) -> None:
        super().__init__(master, bg=T.SIDEBAR, width=220, **kwargs)
        self.pack_propagate(False)
        self._on_new = on_new
        self._on_select = on_select
        self._rows: list[tk.Frame] = []

        tk.Label(
            self, text=product.upper(), font=T.FONT_TITLE,
            fg=T.ACCENT, bg=T.SIDEBAR,
        ).pack(anchor="w", padx=16, pady=(18, 12))

        new_btn = tk.Frame(self, bg=T.SIDEBAR, highlightbackground=T.ACCENT, highlightthickness=1)
        new_btn.pack(fill="x", padx=12, pady=(0, 14))
        tk.Button(
            new_btn, text="+  New Discussion", font=T.FONT_UI_BOLD,
            fg=T.ACCENT, bg=T.SIDEBAR, activeforeground=T.TEXT,
            activebackground=T.SIDEBAR, bd=0, cursor="hand2",
            command=on_new, pady=8,
        ).pack(fill="x")

        self._list = tk.Frame(self, bg=T.SIDEBAR)
        self._list.pack(fill="both", expand=True, padx=8)
        self.refresh(discussions, active_index)

        foot = tk.Frame(self, bg=T.SIDEBAR, height=44)
        foot.pack(fill="x", side="bottom", pady=8)
        for glyph in ("👤", "⚙", "☾"):
            tk.Label(foot, text=glyph, font=("Segoe UI", 12), fg=T.MUTED, bg=T.SIDEBAR).pack(
                side="left", padx=14
            )

    def refresh(self, discussions: list[str], active_index: int) -> None:
        for w in self._rows:
            w.destroy()
        self._rows.clear()
        for i, title in enumerate(discussions):
            row = tk.Frame(self._list, bg=T.SIDEBAR)
            row.pack(fill="x", pady=2)
            active = i == active_index
            bar = tk.Frame(row, bg=T.ACCENT if active else T.SIDEBAR, width=3)
            bar.pack(side="left", fill="y")
            btn = tk.Button(
                row,
                text=title[:42],
                font=T.FONT_UI_SM,
                fg=T.TEXT if active else T.MUTED,
                bg=T.SURFACE if active else T.SIDEBAR,
                activeforeground=T.TEXT,
                activebackground=T.SURFACE,
                bd=0,
                anchor="w",
                padx=10,
                pady=8,
                cursor="hand2",
                command=lambda idx=i: self._on_select(idx),
            )
            btn.pack(side="left", fill="x", expand=True)
            self._rows.append(row)
