"""
ui.py — Interface graphique Nadia Desktop.

Fenêtre chat minimaliste aux couleurs ALNUA.
Voix activable via bouton micro.
"""

from __future__ import annotations

import logging
import queue
import re
import threading
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
from typing import Callable

logger = logging.getLogger(__name__)


def _strip_markdown(text: str) -> str:
    """Supprime les symboles Markdown pour affichage propre dans tkinter."""
    # Gras **texte** ou *texte*
    text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text, flags=re.DOTALL)
    # Italique _texte_
    text = re.sub(r'_{1,2}(.*?)_{1,2}', r'\1', text, flags=re.DOTALL)
    # Code `texte`
    text = re.sub(r'`{1,3}(.*?)`{1,3}', r'\1', text, flags=re.DOTALL)
    # Titres ## Titre
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    # Bullets - item ou • item → · item
    text = re.sub(r'^\s*[-•]\s*', '  · ', text, flags=re.MULTILINE)
    # Lignes vides multiples
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


class NadiaWindow:
    """Fenêtre principale de Nadia Desktop."""

    def __init__(
        self,
        on_send:    "Callable[[str], None]",
        on_mic_toggle: "Callable[[], None]",
        mic_enabled: bool = False,
    ) -> None:
        self.on_send       = on_send
        self.on_mic_toggle = on_mic_toggle
        self.mic_enabled   = mic_enabled
        self._response_q: queue.Queue[str] = queue.Queue()

        self._build()

    # ── Construction UI ──────────────────────────────────────────────────────

    def _build(self) -> None:
        from nadia_config import (
            THEME_ACCENT, THEME_BG, THEME_MUTED,
            THEME_SURFACE, THEME_TEXT, WINDOW_HEIGHT,
            WINDOW_TITLE, WINDOW_WIDTH,
        )

        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(False, True)
        self.root.configure(bg=THEME_BG)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # ── Header ───────────────────────────────────────────────────────────
        header = tk.Frame(self.root, bg=THEME_SURFACE, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="NADIA",
            font=("Space Grotesk", 14, "bold"),
            fg=THEME_ACCENT,
            bg=THEME_SURFACE,
        ).pack(side="left", padx=16, pady=10)

        self._status_var = tk.StringVar(value="● Hub")
        self._status_lbl = tk.Label(
            header,
            textvariable=self._status_var,
            font=("Inter", 9),
            fg=THEME_MUTED,
            bg=THEME_SURFACE,
        )
        self._status_lbl.pack(side="right", padx=16)

        tk.Label(
            header,
            text="Secrétaire de direction · ALNUA",
            font=("Inter", 9),
            fg=THEME_MUTED,
            bg=THEME_SURFACE,
        ).pack(side="left")

        # ── Zone de chat ─────────────────────────────────────────────────────
        self._chat = scrolledtext.ScrolledText(
            self.root,
            bg=THEME_BG,
            fg=THEME_TEXT,
            font=("Inter", 10),
            wrap=tk.WORD,
            bd=0,
            padx=12,
            pady=8,
            state="disabled",
            insertbackground=THEME_ACCENT,
        )
        self._chat.pack(fill="both", expand=True, padx=0, pady=0)

        # Tags couleur
        self._chat.tag_config("nadia",  foreground=THEME_ACCENT, font=("Inter", 10, "bold"))
        self._chat.tag_config("emilie", foreground=THEME_TEXT,   font=("Inter", 10, "bold"))
        self._chat.tag_config("time",   foreground=THEME_MUTED,  font=("Inter", 8))
        self._chat.tag_config("msg",    foreground=THEME_TEXT,   font=("Inter", 10))
        self._chat.tag_config("system", foreground=THEME_MUTED,  font=("Inter", 9, "italic"))

        # ── Barre de saisie ──────────────────────────────────────────────────
        bar = tk.Frame(self.root, bg=THEME_SURFACE, height=56)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        # Bouton micro
        self._mic_btn = tk.Button(
            bar,
            text="🎤",
            font=("Inter", 14),
            bg=THEME_SURFACE,
            fg=THEME_MUTED,
            activebackground=THEME_SURFACE,
            activeforeground=THEME_ACCENT,
            bd=0,
            cursor="hand2",
            command=self._toggle_mic,
        )
        self._mic_btn.pack(side="left", padx=8)

        # Champ texte
        self._entry = tk.Entry(
            bar,
            bg=THEME_BG,
            fg=THEME_TEXT,
            font=("Inter", 11),
            bd=0,
            insertbackground=THEME_ACCENT,
            relief="flat",
        )
        self._entry.pack(side="left", fill="x", expand=True, ipady=8)
        self._entry.bind("<Return>", self._on_enter)
        self._entry.focus()

        # Bouton envoyer
        tk.Button(
            bar,
            text="↑",
            font=("Inter", 14, "bold"),
            bg=THEME_ACCENT,
            fg=THEME_BG,
            activebackground=THEME_TEXT,
            bd=0,
            padx=14,
            cursor="hand2",
            command=self._on_send_click,
        ).pack(side="right", pady=6, padx=6)

        # Message de bienvenue
        self._append_nadia(
            "Bonjour Emilie. Je suis là — dis-moi ce dont tu as besoin "
            "(mails, agenda, contrat, délégation à l'équipe…)."
        )

        # Polling des réponses async
        self.root.after(100, self._poll_responses)

    # ── Actions ──────────────────────────────────────────────────────────────

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

    # ── Affichage messages ───────────────────────────────────────────────────

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

    def _append_system(self, text: str) -> None:
        self._chat.config(state="normal")
        self._chat.insert(tk.END, f"\n{text}\n", "system")
        self._chat.config(state="disabled")
        self._chat.see(tk.END)

    def _set_status(self, text: str) -> None:
        self._status_var.set(text)

    # ── API publique ─────────────────────────────────────────────────────────

    def push_response(self, text: str) -> None:
        """Thread-safe : enqueue une réponse de Nadia."""
        self._response_q.put(text)

    def push_stt_text(self, text: str) -> None:
        """Appelé depuis le thread STT — affiche la transcription."""
        self._response_q.put(f"__STT__{text}")

    def set_hub_mode(self, mode: str) -> None:
        labels = {
            "hub":        "● Hub",
            "glm_direct": "● GLM-5.2",
            "ollama":     "● Ollama",
            "offline":    "○ Offline",
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
