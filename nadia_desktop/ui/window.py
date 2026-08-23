"""
ui/window.py — ALNUA Desk (Spark) — layout maquette AETHER / palette ALNUA.
"""

from __future__ import annotations

import logging
import queue
import re
import tkinter as tk
from datetime import datetime
from tkinter import scrolledtext
from typing import Any, Callable

from ui import theme as T
from ui.composer import DeskComposer
from ui.sidebar import DeskSidebar

logger = logging.getLogger(__name__)


def _strip_markdown(text: str) -> str:
    text = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"_{1,2}(.*?)_{1,2}", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"`{1,3}(.*?)`{1,3}", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-•]\s*", "  · ", text, flags=re.MULTILINE)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


class NadiaWindow:
    """Shell maquette : sidebar + chat + toggles Deep Search / PC Access."""

    def __init__(
        self,
        on_send: Callable[[str, dict[str, Any]], None],
        on_mic_toggle: Callable[[], None],
        *,
        mic_enabled: bool = False,
    ) -> None:
        self.on_send = on_send
        self.on_mic_toggle = on_mic_toggle
        self.mic_enabled = mic_enabled
        self._response_q: queue.Queue[str] = queue.Queue()
        self._discussions = ["Nouvelle discussion"]
        self._active = 0
        self._deep_search = True
        self._pc_access = True
        self._build()

    def _build(self) -> None:
        from nadia_config import PRODUCT_NAME, PRODUCT_TAGLINE, WINDOW_HEIGHT, WINDOW_TITLE, WINDOW_WIDTH

        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(900, 600)
        self.root.configure(bg=T.BG)
        self.root.protocol("WM_DELETE_WINDOW", lambda: self.root.destroy())
        # X rond ALNUA (barre des taches / titre)
        try:
            from pathlib import Path

            ico = Path(__file__).resolve().parents[2] / "assets" / "alnua-x-round.ico"
            if ico.exists():
                self.root.iconbitmap(default=str(ico))
        except Exception:
            pass

        shell = tk.Frame(self.root, bg=T.BG)
        shell.pack(fill="both", expand=True)
        self._sidebar = DeskSidebar(
            shell, product=PRODUCT_NAME, on_new=self._new_discussion,
            on_select=self._select_discussion, discussions=self._discussions,
            active_index=self._active,
        )
        self._sidebar.pack(side="left", fill="y")
        main = tk.Frame(shell, bg=T.BG)
        main.pack(side="left", fill="both", expand=True)
        self._build_header(main, PRODUCT_NAME, PRODUCT_TAGLINE)
        self._build_chat(main)
        self._composer = DeskComposer(
            main, on_send=self._on_send_click, on_mic=self._toggle_mic,
            on_deep=self._toggle_deep, on_pc=self._toggle_pc,
        )
        self._composer.pack(fill="x", side="bottom")
        self._composer.entry.focus()
        self._append_system(
            "Bonjour Emilie. Spark est prêt — Deep Search et Accès PC activés. "
            "Joins un fichier ou pose ta question."
        )
        self.root.after(100, self._poll_responses)

    def _build_header(self, parent: tk.Frame, product: str, tagline: str) -> None:
        header = tk.Frame(parent, bg=T.SURFACE, height=48)
        header.pack(fill="x")
        header.pack_propagate(False)
        left = tk.Frame(header, bg=T.SURFACE)
        left.pack(side="left", padx=16)
        tk.Label(left, text="●", font=("Segoe UI", 9), fg=T.OK, bg=T.SURFACE).pack(side="left")
        tk.Label(
            left, text=f"  {product} · {tagline} (Actif)", font=T.FONT_UI_BOLD,
            fg=T.TEXT, bg=T.SURFACE,
        ).pack(side="left")
        self._status_right = tk.StringVar()
        self._refresh_status_right()
        tk.Label(
            header, textvariable=self._status_right, font=T.FONT_UI_SM,
            fg=T.MUTED, bg=T.SURFACE,
        ).pack(side="right", padx=16)

    def _refresh_status_right(self) -> None:
        pc = "Actif" if self._pc_access else "Off"
        ds = "Connecté" if self._deep_search else "Off"
        self._status_right.set(f"Accès PC: {pc}  |  Deep Search: {ds}")

    def _build_chat(self, parent: tk.Frame) -> None:
        wrap = tk.Frame(parent, bg=T.BG)
        wrap.pack(fill="both", expand=True, padx=16, pady=8)
        self._chat = scrolledtext.ScrolledText(
            wrap, bg=T.BG, fg=T.TEXT, font=T.FONT_UI, wrap=tk.WORD,
            bd=0, padx=8, pady=8, state="disabled", insertbackground=T.ACCENT,
            highlightthickness=0,
        )
        self._chat.pack(fill="both", expand=True)
        for tag, kw in (
            ("user_lbl", {"foreground": T.MUTED, "font": T.FONT_UI_SM}),
            ("user", {"foreground": T.TEXT, "font": T.FONT_UI, "background": T.USER_BUBBLE,
                      "lmargin1": 40, "lmargin2": 40, "rmargin": 12, "spacing1": 4, "spacing3": 8}),
            ("agent_lbl", {"foreground": T.ACCENT, "font": T.FONT_UI_BOLD}),
            ("thought", {"foreground": T.MUTED, "font": T.FONT_UI_SM, "background": T.THOUGHT_BG,
                         "lmargin1": 12, "lmargin2": 20, "spacing1": 2, "spacing3": 2}),
            ("msg", {"foreground": T.TEXT, "font": T.FONT_UI, "spacing1": 2, "spacing3": 6}),
            ("code", {"foreground": "#C8D0DC", "font": T.FONT_MONO, "background": T.CODE_BG,
                      "lmargin1": 12, "lmargin2": 12, "spacing1": 4, "spacing3": 4}),
            ("system", {"foreground": T.MUTED, "font": ("Segoe UI", 9, "italic")}),
            ("time", {"foreground": T.MUTED, "font": ("Segoe UI", 8)}),
        ):
            self._chat.tag_config(tag, **kw)

    def _toggle_deep(self) -> None:
        self._deep_search = not self._deep_search
        self._composer.paint_toggle(self._composer.ds_btn, "Deep Search", self._deep_search)
        self._refresh_status_right()

    def _toggle_pc(self) -> None:
        self._pc_access = not self._pc_access
        self._composer.paint_toggle(self._composer.pc_btn, "PC Access", self._pc_access)
        self._refresh_status_right()

    def _new_discussion(self) -> None:
        self._discussions.insert(0, f"Discussion {len(self._discussions) + 1}")
        self._active = 0
        self._sidebar.refresh(self._discussions, self._active)
        self._chat.config(state="normal")
        self._chat.delete("1.0", tk.END)
        self._chat.config(state="disabled")
        self._append_system("Nouvelle discussion — Spark à l'écoute.")

    def _select_discussion(self, idx: int) -> None:
        self._active = idx
        self._sidebar.refresh(self._discussions, self._active)

    def _on_send_click(self) -> None:
        text = self._composer.entry.get().strip()
        if not text:
            return
        self._composer.entry.delete(0, tk.END)
        self._append_user(text)
        if self._discussions[self._active].startswith(("Nouvelle", "Discussion")):
            self._discussions[self._active] = text[:40]
            self._sidebar.refresh(self._discussions, self._active)
        self._append_thought("> Spark analyse…")
        if self._deep_search:
            self._append_thought("> Deep Search IA en cours…")
        if self._pc_access:
            self._append_thought("> Accès PC : contexte local autorisé")
        att = self._composer.attachment
        if att:
            self._append_thought(f"> Fichier joint : {att.replace(chr(92), '/').split('/')[-1]}")
        self.on_send(text, {
            "deep_search": self._deep_search,
            "pc_access": self._pc_access,
            "attachment": att,
        })

    def _toggle_mic(self) -> None:
        self.mic_enabled = not self.mic_enabled
        self._composer.mic_btn.config(fg=T.ACCENT if self.mic_enabled else T.MUTED)
        self.on_mic_toggle()

    def _ins(self, text: str, *tags: str) -> None:
        self._chat.config(state="normal")
        self._chat.insert(tk.END, text, tags)
        self._chat.config(state="disabled")
        self._chat.see(tk.END)

    def _append_user(self, text: str) -> None:
        self._ins(f"\n{datetime.now().strftime('%H:%M')}  Emilie\n", "user_lbl")
        self._ins(f"{text}\n", "user")

    def _append_thought(self, line: str) -> None:
        self._ins(f"{line}\n", "thought")

    def _append_system(self, text: str) -> None:
        self._ins(f"\n{text}\n", "system")

    def _append_nadia(self, text: str) -> None:
        raw = text
        ts = datetime.now().strftime("%H:%M")
        self._ins(f"\n{ts}  ", "time")
        self._ins("Nadia · Spark\n", "agent_lbl")
        if "```" in raw:
            for i, part in enumerate(raw.split("```")):
                if i % 2 == 0:
                    clean = _strip_markdown(part)
                    if clean:
                        self._ins(f"{clean}\n", "msg")
                else:
                    code = part.split("\n", 1)[-1] if "\n" in part else part
                    self._ins(f"{code.strip()}\n", "code")
        else:
            self._ins(f"{_strip_markdown(text)}\n", "msg")

    def push_response(self, text: str) -> None:
        self._response_q.put(text)

    def push_stt_text(self, text: str) -> None:
        self._response_q.put(f"__STT__{text}")

    def set_hub_mode(self, mode: str) -> None:
        self._response_q.put(f"__STATUS__{mode}")

    def _poll_responses(self) -> None:
        try:
            while True:
                item = self._response_q.get_nowait()
                if item.startswith("__STT__"):
                    self._composer.entry.delete(0, tk.END)
                    self._composer.entry.insert(0, item[7:])
                    self._on_send_click()
                elif item.startswith("__STATUS__"):
                    pass
                else:
                    self._append_nadia(item)
        except Exception:
            pass
        self.root.after(100, self._poll_responses)

    def run(self) -> None:
        self.root.mainloop()
