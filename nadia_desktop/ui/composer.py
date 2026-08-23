"""Composer footer — input + attachment + Deep Search / PC Access toggles."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog
from typing import Callable

from ui import theme as T


class DeskComposer(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        on_send: Callable[[], None],
        on_mic: Callable[[], None],
        on_deep: Callable[[], None],
        on_pc: Callable[[], None],
        deep_on: bool = True,
        pc_on: bool = True,
    ) -> None:
        super().__init__(master, bg=T.SURFACE)
        self._attachment: str | None = None
        self.on_send = on_send

        self._attach_frame = tk.Frame(self, bg=T.SURFACE)
        self._attach_frame.pack(fill="x", padx=16, pady=(10, 0))
        self._attach_var = tk.StringVar(value="")
        self._attach_chip = tk.Label(
            self._attach_frame, textvariable=self._attach_var, font=T.FONT_UI_SM,
            fg=T.ACCENT, bg=T.INPUT_BG, padx=10, pady=4,
        )

        box = tk.Frame(self, bg=T.ACCENT, padx=1, pady=1)
        box.pack(fill="x", padx=16, pady=(8, 6))
        inner = tk.Frame(box, bg=T.INPUT_BG)
        inner.pack(fill="x")
        tk.Button(
            inner, text="📎", font=("Segoe UI", 12), bg=T.INPUT_BG, fg=T.MUTED,
            activebackground=T.INPUT_BG, activeforeground=T.ACCENT, bd=0,
            cursor="hand2", command=self._pick_file,
        ).pack(side="left", padx=6)
        self.entry = tk.Entry(
            inner, bg=T.INPUT_BG, fg=T.TEXT, font=("Segoe UI", 11), bd=0,
            insertbackground=T.ACCENT, relief="flat",
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=10, padx=4)
        self.entry.bind("<Return>", lambda _e: on_send())
        tk.Button(
            inner, text="➤", font=("Segoe UI", 12, "bold"), bg=T.INPUT_BG, fg=T.ACCENT,
            activebackground=T.INPUT_BG, activeforeground=T.TEXT, bd=0, padx=12,
            cursor="hand2", command=on_send,
        ).pack(side="right")

        toggles = tk.Frame(self, bg=T.SURFACE)
        toggles.pack(fill="x", padx=16, pady=(0, 12))
        self.ds_btn = self._toggle(toggles, "Deep Search", deep_on, on_deep)
        self.pc_btn = self._toggle(toggles, "PC Access", pc_on, on_pc)
        self.ds_btn.pack(side="left", padx=(0, 10))
        self.pc_btn.pack(side="left")
        self.mic_btn = tk.Button(
            toggles, text="🎤", font=("Segoe UI", 11), bg=T.SURFACE, fg=T.MUTED,
            activebackground=T.SURFACE, activeforeground=T.ACCENT, bd=0,
            cursor="hand2", command=on_mic,
        )
        self.mic_btn.pack(side="right")

    @staticmethod
    def _toggle(parent: tk.Frame, label: str, on: bool, cmd: Callable) -> tk.Button:
        return tk.Button(
            parent, text=f"{label}  {'ON' if on else 'OFF'}", font=T.FONT_UI_SM,
            fg=T.ACCENT if on else T.MUTED, bg=T.INPUT_BG,
            activeforeground=T.TEXT, activebackground=T.INPUT_BG,
            bd=0, padx=12, pady=6, cursor="hand2",
            highlightbackground=T.ACCENT if on else T.BORDER,
            highlightthickness=1, command=cmd,
        )

    def paint_toggle(self, btn: tk.Button, label: str, on: bool) -> None:
        btn.config(
            text=f"{label}  {'ON' if on else 'OFF'}",
            fg=T.ACCENT if on else T.MUTED,
            highlightbackground=T.ACCENT if on else T.BORDER,
        )

    def _pick_file(self) -> None:
        path = filedialog.askopenfilename(title="Joindre un fichier")
        if not path:
            return
        name = path.replace("\\", "/").split("/")[-1]
        self._attachment = path
        self._attach_var.set(f"Active file attachment: {name}")
        self._attach_chip.pack(anchor="w")

    @property
    def attachment(self) -> str | None:
        return self._attachment
