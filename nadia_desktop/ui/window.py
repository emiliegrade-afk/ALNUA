"""
ui/window.py — Interface graphique Nadia Desktop (chat only).

Le traitement de texte / contrats vit dans le Hub (/secretary), pas ici.
"""

from __future__ import annotations

import logging
import queue
import re
import tkinter as tk
from datetime import datetime
from tkinter import scrolledtext
from typing import Callable

logger = logging.getLogger(__name__)


def _strip_markdown(text: str) -> str:
    text = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"_{1,2}(.*?)_{1,2}", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"`{1,3}(.*?)`{1,3}", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-•]\s*", "  · ", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


class NadiaWindow:
    """Fenêtre principale — chat uniquement."""

    def __init__(
        self,
        on_send: Callable[[str], None],
        on_mic_toggle: Callable[[], None],
        *,
        mic_enabled: bool = False,
    ) -> None:
        self.on_send = on_send
        self.on_mic_toggle = on_mic_toggle
        self.mic_enabled = mic_enabled
        self._response_q: queue.Queue[str] = queue.Queue()
        self._build()

    def _build(self) -> None:
        from nadia_config import (
            THEME_ACCENT,
            THEME_BG,
            THEME_MUTED,
            THEME_SURFACE,
            THEME_TEXT,
            WINDOW_HEIGHT,
            WINDOW_TITLE,
            WINDOW_WIDTH,
        )

        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(True, True)
        self.root.configure(bg=THEME_BG)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        header = tk.Frame(self.root, bg=THEME_SURFACE, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header, text="NADIA", font=("Space Grotesk", 14, "bold"),
            fg=THEME_ACCENT, bg=THEME_SURFACE,
        ).pack(side="left", padx=16, pady=10)
        self._status_var = tk.StringVar(value="● Hub")
        tk.Label(
            header, textvariable=self._status_var, font=("Inter", 9),
            fg=THEME_MUTED, bg=THEME_SURFACE,
        ).pack(side="right", padx=16)
        tk.Label(
            header, text="Assistante · Hub", font=("Inter", 9),
            fg=THEME_MUTED, bg=THEME_SURFACE,
        ).pack(side="left")

        self._chat = scrolledtext.ScrolledText(
            self.root, bg=THEME_BG, fg=THEME_TEXT, font=("Inter", 10),
            wrap=tk.WORD, bd=0, padx=12, pady=8, state="disabled",
            insertbackground=THEME_ACCENT,
        )
        self._chat.pack(fill="both", expand=True)
        for tag, kw in (
            ("nadia", {"foreground": THEME_ACCENT, "font": ("Inter", 10, "bold")}),
            ("emilie", {"foreground": THEME_TEXT, "font": ("Inter", 10, "bold")}),
            ("time", {"foreground": THEME_MUTED, "font": ("Inter", 8)}),
            ("msg", {"foreground": THEME_TEXT, "font": ("Inter", 10)}),
            ("system", {"foreground": THEME_MUTED, "font": ("Inter", 9, "italic")}),
        ):
            self._chat.tag_config(tag, **kw)

        bar = tk.Frame(self.root, bg=THEME_SURFACE, height=56)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        self._mic_btn = tk.Button(
            bar, text="🎤", font=("Inter", 14), bg=THEME_SURFACE, fg=THEME_MUTED,
            activebackground=THEME_SURFACE, activeforeground=THEME_ACCENT, bd=0,
            cursor="hand2", command=self._toggle_mic,
        )
        self._mic_btn.pack(side="left", padx=8)
        self._entry = tk.Entry(
            bar, bg=THEME_BG, fg=THEME_TEXT, font=("Inter", 11), bd=0,
            insertbackground=THEME_ACCENT, relief="flat",
        )
        self._entry.pack(side="left", fill="x", expand=True, ipady=8)
        self._entry.bind("<Return>", self._on_enter)
        self._entry.focus()
        tk.Button(
            bar, text="↑", font=("Inter", 14, "bold"), bg=THEME_ACCENT, fg=THEME_BG,
            activebackground=THEME_TEXT, bd=0, padx=14, cursor="hand2",
            command=self._on_send_click,
        ).pack(side="right", pady=6, padx=6)

        self._append_nadia(
            "Bonjour Emilie. Docs et contrats : dans le Hub Secrétariat. "
            "Ici on parle — mails, agenda, recherches, délégation…"
        )
        self.root.after(100, self._poll_responses)

    def _on_enter(self, event=None) -> None:
        self._on_send_click()

    def _on_send_click(self) -> None:
        text = self._entry.get().strip()
        if not text:
            return
        self._entry.delete(0, tk.END)
        self._append_emilie(text)
        self._set_status("⏳ Nadia réfléchit…")
        self.on_send(text)

    def _toggle_mic(self) -> None:
        self.mic_enabled = not self.mic_enabled
        from nadia_config import THEME_ACCENT, THEME_MUTED

        self._mic_btn.config(fg=THEME_ACCENT if self.mic_enabled else THEME_MUTED)
        self.on_mic_toggle()

    def _on_close(self) -> None:
        self.root.destroy()

    def _append_emilie(self, text: str) -> None:
        self._chat.config(state="normal")
        ts = datetime.now().strftime("%H:%M")
        self._chat.insert(tk.END, f"\n{ts}  ", "time")
        self._chat.insert(tk.END, "Emilie  ", "emilie")
        self._chat.insert(tk.END, f"{text}\n", "msg")
        self._chat.config(state="disabled")
        self._chat.see(tk.END)

    def _append_nadia(self, text: str) -> None:
        text = _strip_markdown(text)
        self._chat.config(state="normal")
        ts = datetime.now().strftime("%H:%M")
        self._chat.insert(tk.END, f"\n{ts}  ", "time")
        self._chat.insert(tk.END, "Nadia  ", "nadia")
        self._chat.insert(tk.END, f"{text}\n", "msg")
        self._chat.config(state="disabled")
        self._chat.see(tk.END)

    def _set_status(self, text: str) -> None:
        self._status_var.set(text)

    def push_response(self, text: str) -> None:
        self._response_q.put(text)

    def push_stt_text(self, text: str) -> None:
        self._response_q.put(f"__STT__{text}")

    def set_hub_mode(self, mode: str) -> None:
        labels = {
            "hub": "● Hub",
            "glm_direct": "● GLM-5.2",
            "ollama": "● Ollama",
            "offline": "○ Offline",
        }
        self._response_q.put(f"__STATUS__{labels.get(mode, mode)}")

    def _poll_responses(self) -> None:
        try:
            while True:
                item = self._response_q.get_nowait()
                if item.startswith("__STT__"):
                    text = item[7:]
                    self._entry.delete(0, tk.END)
                    self._entry.insert(0, text)
                    self._on_send_click()
                elif item.startswith("__STATUS__"):
                    self._set_status(item[10:])
                else:
                    self._append_nadia(item)
                    self._set_status("● Hub")
        except Exception:
            pass
        self.root.after(100, self._poll_responses)

    def run(self) -> None:
        self.root.mainloop()
