"""Contract template registry — metadata + article scaffolds (not legal gospel)."""

from __future__ import annotations

from typing import Any

from config.contract_template_bodies import body_for

# Types évolutifs — corps détaillés dans contract_template_bodies.py.
CONTRACT_TEMPLATES: dict[str, dict[str, Any]] = {
    "nda": {
        "id": "nda",
        "label": "NDA / Confidentialité",
        "jurisdictions": ["UE", "USA"],
        "articles": [
            "Objet et définitions",
            "Informations confidentielles",
            "Exceptions",
            "Durée",
            "Restitution / destruction",
            "Droit applicable",
        ],
    },
    "partenariat": {
        "id": "partenariat",
        "label": "Partenariat marque",
        "jurisdictions": ["UE", "USA", "ASIE"],
        "articles": [
            "Objet du partenariat",
            "Obligations ALNUA",
            "Obligations partenaire",
            "Propriété intellectuelle",
            "Rémunération / contreparties",
            "Durée et résiliation",
            "Droit applicable",
        ],
    },
    "influenceur": {
        "id": "influenceur",
        "label": "Contrat influenceur / créateur",
        "jurisdictions": ["UE", "USA"],
        "articles": [
            "Objet et livrables",
            "Mention publicitaire / transparence",
            "Droits d'image et d'utilisation",
            "Rémunération",
            "Exclusivité",
            "Résiliation",
            "Droit applicable",
        ],
    },
    "pub": {
        "id": "pub",
        "label": "Contrat publicité / media (Meta, Google, TikTok…)",
        "jurisdictions": ["UE", "USA", "ASIE"],
        "articles": [
            "Objet campagne",
            "Budgets et plafonds",
            "Créatifs et validations",
            "Données / tracking / privacy",
            "Reporting",
            "Responsabilité",
            "Droit applicable",
        ],
    },
    "prestation": {
        "id": "prestation",
        "label": "Prestation / freelance",
        "jurisdictions": ["UE"],
        "articles": [
            "Objet et livrables",
            "Planning",
            "Rémunération et frais",
            "IP et cession",
            "Confidentialité",
            "Résiliation",
            "Droit applicable",
        ],
    },
    "affiliation": {
        "id": "affiliation",
        "label": "Affiliation",
        "jurisdictions": ["UE", "USA"],
        "articles": [
            "Objet programme",
            "Commissions",
            "Tracking et attribution",
            "Interdictions",
            "Paiements",
            "Résiliation",
            "Droit applicable",
        ],
    },
    "freelance": {
        "id": "freelance",
        "label": "Freelance (alias prestation)",
        "alias_of": "prestation",
        "jurisdictions": ["UE"],
        "articles": [],
    },
}


def list_contract_templates() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for tid, meta in CONTRACT_TEMPLATES.items():
        if meta.get("alias_of"):
            continue
        out.append(
            {
                "id": tid,
                "label": meta.get("label"),
                "jurisdictions": meta.get("jurisdictions") or [],
                "article_titles": list(meta.get("articles") or []),
                "has_body": bool(body_for(tid)),
            }
        )
    return out


def resolve_template(contract_type: str) -> dict[str, Any] | None:
    key = (contract_type or "").strip().lower()
    meta = CONTRACT_TEMPLATES.get(key)
    if not meta:
        return None
    alias = meta.get("alias_of")
    if alias:
        return resolve_template(str(alias))
    return {**meta, "body": body_for(str(meta.get("id") or key))}


def template_prompt_block(contract_type: str) -> str:
    meta = resolve_template(contract_type)
    if not meta:
        known = ", ".join(sorted(k for k, v in CONTRACT_TEMPLATES.items() if not v.get("alias_of")))
        return f"Type inconnu. Types connus : {known}."
    arts = meta.get("articles") or []
    lines = [f"Template « {meta.get('label')} » (id={meta.get('id')})."]
    lines.append(f"Juridictions cibles : {', '.join(meta.get('jurisdictions') or [])}.")
    lines.append("Structure d'articles attendue :")
    for i, title in enumerate(arts, 1):
        lines.append(f"  {i}. {title}")
    body = (meta.get("body") or "").strip()
    if body:
        lines.append("\n--- Scaffold détaillé (adapte, ne copie pas aveuglément) ---")
        lines.append(body)
    lines.append(
        "\nAdapte le contenu aux parties réelles ; ce n'est pas un modèle juridique "
        "opposable. Prévoir relecture avocat ALNUA (Solène) avant signature."
    )
    return "\n".join(lines)
