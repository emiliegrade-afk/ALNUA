"""Prompts for R&D dossier committee (phase 3)."""

from __future__ import annotations

from config.agent_operating_spec import build_committee_system_prompt

COMMITTEE_RULES = """
RÈGLES DU COMITÉ R&D ALNUA :
- Tu parles en français, ton direct et professionnel (réunion produit, pas marketing creux).
- Max 120 mots par intervention — une idée forte, une objection ou une recommandation.
- Cite le dossier : sections, chiffres finance, MVP, risques. Pas de généralités.
- INTERDIT : "marché énorme", "les X vont adorer", chiffres sans source.
- Si tu n'es pas d'accord avec un collègue, dis-le explicitement et pourquoi.
- Termine souvent par une action concrète pour Emilie (valider, couper, tester, différer).
"""

# Kept for tests / docs — overlay is in rnd_committee_overlay spec.
MEMBER_PERSONAS: dict[str, str] = {}


def build_member_system(member_id: str, dossier_context: str) -> str:
    return build_committee_system_prompt(member_id, dossier_context)


KICKOFF_USER = """Le comité R&D vient de s'ouvrir sur ce dossier.
Chaque membre listé doit donner une prise de position initiale (2-3 phrases max).
Couvre : opportunité réelle, plus gros risque, première action recommandée.

Membres : {members}

Réponds UNIQUEMENT en JSON :
{{
  "openings": [
    {{"speaker": "pm", "content": "..."}},
    ...
  ]
}}"""


CHOOSE_RESPONDERS_USER = """Message d'Emilie dans le comité :
"{message}"

Équipe disponible : {members}
Section active : {active_section}

Choisis 1 à 3 membres qui doivent répondre (ceux les plus pertinents).
Réponds UNIQUEMENT en JSON : {{ "responders": ["pm", "marketing"] }}"""
