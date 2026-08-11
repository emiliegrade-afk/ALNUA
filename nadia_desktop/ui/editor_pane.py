"""Nadia Desktop — panneau éditeur de documents (markdown)."""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import scrolledtext, messagebox
from typing import Any, Callable

logger = logging.getLogger(__name__)


class DocEditorPane(tk.Frame):
    """Simple markdown editor bound to Hub data/nadia_docs via callbacks."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        on_save: Callable[[str, str, str | None], dict[str, Any] | None],
        on_list: Callable[[], list[dict[str, Any]]],
        on_load: Callable[[str], dict[str, Any] | None],
        colors: dict[str, str],
    ) -> None:
        super().__init__(master, bg=colors.get("bg", "#0E1014"))
        self._on_save = on_save
        self._on_list = on_list
        self._on_load = on_load
        self._colors = colors
        self._doc_id: str | None = None

        toolbar = tk.Frame(self, bg=colors.get("bg", "#0E1014"))
        toolbar.pack(fill="x", padx=4, pady=4)
        tk.Button(toolbar, text="Nouveau", command=self._new, bg="#E09B6A", fg="#0E1014").pack(
            side="left", padx=2
        )
        tk.Button(toolbar, text="Ouvrir…", command=self._pick, bg="#2A2E38", fg="#F5F2EA").pack(
            side="left", padx=2
        )
        tk.Button(toolbar, text="Sauver", command=self._save, bg="#2A2E38", fg="#F5F2EA").pack(
            side="left", padx=2
        )

        self._title = tk.Entry(self, bg="#16181D", fg="#F5F2EA", insertbackground="#F5F2EA")
        self._title.pack(fill="x", padx=4, pady=(0, 4))
        self._title.insert(0, "Sans titre")

        self._body = scrolledtext.ScrolledText(
            self,
            wrap="word",
            bg="#16181D",
            fg="#F5F2EA",
            insertbackground="#F5F2EA",
            font=("Consolas", 10),
        )
        self._body.pack(fill="both", expand=True, padx=4, pady=4)

    def _new(self) -> None:
        self._doc_id = None
        self._title.delete(0, "end")
        self._title.insert(0, "Nouvelle note")
        self._body.delete("1.0", "end")
        self._body.insert("1.0", "# Nouvelle note\n\n")

    def _pick(self) -> None:
        try:
            docs = self._on_list()
        except Exception as exc:
            messagebox.showerror("Nadia", f"Liste docs impossible : {exc}")
            return
        if not docs:
            messagebox.showinfo("Nadia", "Aucun document — crée-en un.")
            return
        # Simple first-doc picker for v2; expand later
        top = docs[0]
        doc = self._on_load(str(top.get("id")))
        if not doc:
            return
        self._doc_id = str(doc.get("id"))
        self._title.delete(0, "end")
        self._title.insert(0, str(doc.get("title") or self._doc_id))
        self._body.delete("1.0", "end")
        self._body.insert("1.0", doc.get("content") or "")

    def _save(self) -> None:
        title = self._title.get().strip() or "Sans titre"
        content = self._body.get("1.0", "end-1c")
        try:
            result = self._on_save(self._doc_id or "", content, title)
        except Exception as exc:
            messagebox.showerror("Nadia", f"Sauve échouée : {exc}")
            return
        if result:
            self._doc_id = str(result.get("id"))
            messagebox.showinfo("Nadia", f"Enregistré : {result.get('path')}")

    def set_content(self, title: str, content: str, doc_id: str | None = None) -> None:
        self._doc_id = doc_id
        self._title.delete(0, "end")
        self._title.insert(0, title)
        self._body.delete("1.0", "end")
        self._body.insert("1.0", content)
