"""Bureau / room standards snippets for L2 (DEC-027)."""

from __future__ import annotations

ROOM_STANDARDS: dict[str, tuple[str, ...]] = {
    "direction": (
        "Décisions CEO/COO tracées ; pas de ship sans gate QA quand code.",
        "Escalade ECART / A_VERIFIER plutôt que contourner la policy.",
    ),
    "app_office": (
        "PR feature only ; merge staging via intégrateur ; tests avant review.",
        "Worktree obligatoire pour side-effects code.",
    ),
    "gaming_studio": (
        "GDD / agency UE ou Godot selon DEC projet ; pas de push main solo.",
    ),
    "rnd_lab": (
        "Dossiers via pipeline R&D ; ready_for_ceo seulement après gates.",
    ),
    "comms_hub": (
        "Publish / ads = humain ou capability ads:spend ; pas de spam.",
    ),
    "accounting_office": (
        "Pas de transfert budget / paiement sans validation.",
    ),
    "hardware_workshop": (
        "Pas de commande hardware destructrice depuis idle L1.",
    ),
    "analytics_room": (
        "Insights actionnables ; pas de décision business auto.",
    ),
    "secretary_office": (
        "Filtrage et agenda ; mail:send seulement avec capability.",
    ),
}


def l2_standards_block(room_id: str | None, *, max_chars: int = 500) -> str:
    key = (room_id or "").strip() or "direction"
    rules = ROOM_STANDARDS.get(key) or ROOM_STANDARDS.get("direction") or ()
    if not rules:
        return ""
    lines = "\n".join(f"- {r}" for r in rules)
    block = (
        f"\n\n─── L2 STANDARDS BUREAU (`{key}`) ───\n"
        f"{lines}\n"
        "─── Fin L2 standards ───"
    )
    return block if len(block) <= max_chars else block[: max_chars - 24] + "\n─── Fin L2 standards ───"
