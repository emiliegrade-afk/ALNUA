#!/usr/bin/env python3
"""Migrate agent classes to AgentBase + _complete() with canonical llm_agent_id."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "agents"
SKIP = {"agent_base.py", "base.py", "fix_pipeline.py", "coo_agent.py", "rnd_ceo_agent.py"}


def migrate_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    original = text

    if "self.llm.complete" not in text:
        return False

    if "from agents.agent_base import AgentBase" not in text:
        if "from __future__ import annotations" in text:
            text = text.replace(
                "from __future__ import annotations\n",
                "from __future__ import annotations\n\nfrom agents.agent_base import AgentBase\n",
                1,
            )
        else:
            text = "from agents.agent_base import AgentBase\n\n" + text

    text = re.sub(
        r"class (\w+Agent)\s*(?:\([^)]*\))?\s*:",
        r"class \1(AgentBase):",
        text,
        count=1,
    )

    # Remove boilerplate __init__ that only sets db/llm
    text = re.sub(
        r"\n    def __init__\(self(?:, db: [^)]*)?\) -> None:\n"
        r"        self\.db = db or get_supabase\(\)\n"
        r"        self\.llm = llm or LLMClient\(\)\n",
        "\n",
        text,
    )
    text = re.sub(
        r"\n    def __init__\(self\) -> None:\n"
        r"        self\.db = get_supabase\(\)\n"
        r"        self\.llm = LLMClient\(\)\n",
        "\n",
        text,
    )

    # Multiline complete: self.llm.complete(\n  self.SYSTEM_PROMPT, prompt, agent_id=..., ...)
    def repl_multiline(m: re.Match) -> str:
        prompt = m.group(1).strip()
        rest = m.group(2) or ""
        kwargs: list[str] = []
        for part in re.finditer(r"(temperature|max_tokens)\s*=\s*([^,\n)]+)", rest):
            kwargs.append(f"{part.group(1)}={part.group(2).strip()}")
        if kwargs:
            return f"self._complete({prompt}, {', '.join(kwargs)})"
        return f"self._complete({prompt})"

    text = re.sub(
        r"self\.llm\.complete\(\s*self\.SYSTEM_PROMPT,\s*([^,]+),\s*agent_id=[^,\n)]+([^)]*)\)",
        repl_multiline,
        text,
        flags=re.DOTALL,
    )

    # SYSTEM_PROMPT variable (accountant)
    text = re.sub(
        r"self\.llm\.complete\(\s*SYSTEM_PROMPT,\s*([^,]+),\s*agent_id=[^,\n)]+([^)]*)\)",
        lambda m: repl_multiline(
            type("M", (), {"group": lambda self, i: m.group(i)})()  # noqa: SLF001
        )
        if False
        else (
            f"self._complete({m.group(1).strip()}, "
            + ", ".join(
                f"{p.group(1)}={p.group(2).strip()}"
                for p in re.finditer(
                    r"(temperature|max_tokens)\s*=\s*([^,\n)]+)", m.group(2) or ""
                )
            )
            + ")"
            if re.search(r"(temperature|max_tokens)", m.group(2) or "")
            else f"self._complete({m.group(1).strip()})"
        ),
        text,
        flags=re.DOTALL,
    )

    # return self.llm.complete(...)
    text = re.sub(
        r"return self\.llm\.complete\(\s*self\.SYSTEM_PROMPT,\s*([^,]+),\s*agent_id=[^,\n)]+([^)]*)\)",
        lambda m: "return " + repl_multiline(m),
        text,
        flags=re.DOTALL,
    )

    # Generic remaining: self.llm.complete(self.SYSTEM_PROMPT, X)
    text = re.sub(
        r"self\.llm\.complete\(\s*self\.SYSTEM_PROMPT,\s*([^)]+)\)",
        r"self._complete(\1)",
        text,
    )

    if text == original:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def main() -> None:
    changed = 0
    for path in sorted(ROOT.glob("*_agent.py")):
        if path.name in SKIP:
            continue
        if migrate_file(path):
            print(f"OK {path.name}")
            changed += 1
    print(f"Migrated {changed} files")


if __name__ == "__main__":
    main()
