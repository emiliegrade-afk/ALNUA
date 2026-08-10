"""AgentPlaybook dataclass for R&D workspace dispatch."""

from __future__ import annotations


class AgentPlaybook:
    """Playbook immutable pour un agent dispatch."""

    def __init__(
        self,
        pole: str,
        files: list[str],
        description: str,
        template: str,
        dod: list[str],
    ) -> None:
        self.pole = pole
        self.files = files  # chemins relatifs au projet root
        self.description = description
        self.template = template  # prompt instructions pour le LLM
        self.dod = dod

    def primary_file(self) -> str:
        return self.files[0] if self.files else ""

    def pole_relative_filename(self, idx: int = 0) -> str:
        """Ex: 'direction/spec-cursor-prompt.md' → 'spec-cursor-prompt.md'"""
        f = self.files[idx] if idx < len(self.files) else self.primary_file()
        return f.split("/", 1)[-1] if "/" in f else f
