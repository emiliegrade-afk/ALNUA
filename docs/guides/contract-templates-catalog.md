# Catalogue templates contrats ALNUA (Lot C)

> **Pas figé comme vérité juridique.** Scaffolds pour Nadia (brouillon) +
> relecture obligatoire par **Solène Hariri** (`legal_counsel`) avant signature.
> Disclaimer : l’IA n’est pas un avocat au barreau.

## Types v1

| ID | Label | Juridictions cibles |
|----|-------|---------------------|
| `nda` | NDA / Confidentialité | UE, USA |
| `partenariat` | Partenariat marque | UE, USA, Asie |
| `influenceur` | Influenceur / créateur | UE, USA |
| `pub` | Publicité / media (Meta, Google, TikTok…) | UE, USA, Asie |
| `prestation` | Prestation / freelance | UE |
| `affiliation` | Affiliation | UE, USA |

Alias : `freelance` → `prestation`.

Source code : `config/contract_templates_registry.py`  
API liste : `GET /agents/legal-counsel/templates`

## Flux

1. Emilie / Nadia : brouillon (`draft_contract` ou NL « prépare un contrat… »)
2. Escalade : « fais relire par l’avocat » → `ask_lawyer` / `POST /agents/legal-counsel/review`
3. Emilie lit l’avis → signe **humainement** (hors Hub)

## À enrichir plus tard

- Versions bilingues FR/EN
- Liens vers dossiers `C:\ALNUA\Contrats\…`
- Corps encore plus « cabinet » par juridiction (US state law, etc.)

## Corps v2 (2026-08-11)

Scaffolds détaillés dans `config/contract_template_bodies.py` (injectés dans
`template_prompt_block`) — toujours **brouillons** à faire relire par Solène.
