"""Detailed article scaffolds for contract drafts (not legal gospel)."""

from __future__ import annotations

# Keys = template id. Values = markdown body hints injected into draft prompts.
CONTRACT_BODIES: dict[str, str] = {
    "nda": """\
## Parties
- Divulgateur : [ALNUA / société / Emilie]
- Destinataire : [Nom, forme juridique, siège]

## 1. Objet et définitions
Objet : échange d'informations confidentielles dans le cadre de [projet].
Définitions : Informations Confidentielles, Affiliés, Représentants.

## 2. Informations confidentielles
Inclut : tech, business, clients, finances, code, designs, roadmaps, orales
confirmées par écrit sous 5 jours ouvrés. Marquage « Confidentiel » recommandé
mais non exclusif si caractère conf. évident.

## 3. Exceptions
Domaine public ; déjà détenues licitement ; reçues d'un tiers sans breach ;
révélation légale obligatoire (préavis raisonnable si autorisé).

## 4. Obligations
Non-usage hors objet ; non-divulgation sauf need-to-know ; standard de soin
au moins égal à celui pour ses propres infos sensibles (≥ raisonnable).

## 5. Durée
Accord : [X] ans. Secret : [Y] ans après fin (ou tant que secret commercial).

## 6. Restitution / destruction
Sur demande écrite sous 15 jours : restitution ou destruction + attestation.

## 7. PI
Aucune cession de PI. Feedbacks : licence non exclusive à [Divulgateur] si
acceptés.

## 8. Droit applicable / litiges
[UE : droit français + tribunaux [ville] / USA : État + venue / autre].
""",
    "partenariat": """\
## Parties
ALNUA [entité] ↔ Partenaire [entité] — partenariat marque / co-marketing.

## 1. Objet
Collaboration [description] ; territoires [UE/USA/Asie] ; canaux [liste].

## 2. Obligations ALNUA
Livrables, validations créatives, délais, accès assets brand kit.

## 3. Obligations partenaire
Volumes, mentions, conformité pub locale, reporting.

## 4. Propriété intellectuelle
Chaque partie conserve sa PI préexistante. Créations conjointes : régime
[copropriété / licence croisée] à préciser. Licence d'usage marque limitée
au partenariat, révocable.

## 5. Rémunération / contreparties
[Cash / rev share / barter] — échéancier, devises, taxes.

## 6. Exclusivité
[Aucune / catégorie / territoire / durée].

## 7. Durée et résiliation
Durée initiale + tacite reconduction. Résiliation pour faute (mise en demeure
[X] jours) ou convenience ([Y] jours préavis).

## 8. Confidentialité & data
Renvoi NDA ou clause mini ; RGPD / CCPA si données perso.

## 9. Droit applicable
[Juridiction] + mode de règlement (médiation puis tribunaux / arb.).
""",
    "influenceur": """\
## Parties
ALNUA / marque ↔ Créateur [pseudo, identité civile, contact].

## 1. Objet et livrables
Formats (Reels, Stories, TikTok, YouTube…) ; nombre ; deadlines ; briefs ;
hashtags / mentions obligatoires.

## 2. Transparencé publicitaire
Mentions #ad / #publicité / règles plateforme + droit local (ARPP, FTC…).
Créateur responsable de la conformité d'affichage.

## 3. Droits d'image et d'utilisation
Cession / licence : durée, territoires, médias (paid / organic / ads).
Droit de retrait / moral si UE.

## 4. Rémunération
Montant, échéances (50/50, net 30…), barreaux d'audience optionnels.
Frais remboursables sur justificatifs.

## 5. Exclusivité & non-concurrence
Catégorie concurrents ; durée pendant + post-campagne.

## 6. Approbation & modifications
Circuit validation ALNUA [X] jours ouvrés. Retouches raisonnables incluses.

## 7. Résiliation
Non-livraison, atteinte réputationnelle, breach. Effets sur paiement au prorata.

## 8. Droit applicable
[UE/USA] + litiges.
""",
    "pub": """\
## Parties
Annonceur ALNUA ↔ Agence / media buyer / plateforme (Meta, Google, TikTok…).

## 1. Objet campagne
Objectifs (awareness, leads, sales) ; marchés ; audiences ; dates.

## 2. Budgets et plafonds
Budget total, daily cap, règles de dépassement, devises, frais agence %.

## 3. Créatifs et validations
Ownership assets ; délais validation ; brand safety ; refus raisonnable.

## 4. Données / tracking / privacy
Pixels, CAPI, consentement, DPA si sous-traitance ; interdiction revente data.

## 5. Reporting
Fréquence, KPIs, accès dashboards, audit logs.

## 6. Responsabilité
Plafond = fees payés [X] mois sauf faute lourde / PI / data breach.

## 7. Résiliation
Préavis ; solde des impressions / leads engagés.

## 8. Droit applicable
[UE/USA/Asie] selon marchés ciblés — préciser si multi-juridiction.
""",
    "prestation": """\
## Parties
Client ALNUA ↔ Prestataire [freelance / société].

## 1. Objet et livrables
Cahier des charges annexé ; définition de « Done » ; formats livrés.

## 2. Planning
Jalons, dates, dépendances client ; retards et pénalités optionnelles.

## 3. Rémunération et frais
Honoraires HT/TTV, acomptes, frais pré-approuvés, facturation.

## 4. IP et cession
Cession des droits sur livrables payés (territoire mondial, durée légale max)
sauf outils génériques du prestataire. Code open-source : licences listées.

## 5. Confidentialité
Clause NDA mini ou renvoi NDA séparé.

## 6. Non-sollicitation
Optionnel [X] mois.

## 7. Résiliation
Convenience / faute ; paiement du travail accepté.

## 8. Droit applicable
Droit français / tribunaux [ville] (défaut UE).
""",
    "affiliation": """\
## Parties
ALNUA (merchant) ↔ Affilié [site / créateur / réseau].

## 1. Objet programme
Promotion produits/services ALNUA via liens trackés.

## 2. Commissions
Taux, cookie window, types d'actions (CPA/CPL/RevShare), exclusions.

## 3. Tracking et attribution
Outil, last-click / multi-touch, litiges d'attribution.

## 4. Interdictions
Brand bidding non autorisé, spam, fake traffic, deep links interdits,
contenus illicites / haineux.

## 5. Paiements
Seuil minimum, calendrier, taxes, chargebacks / clawback [X] jours.

## 6. Résiliation
Immédiate pour fraude ; préavis pour convenience. Soldes dus sous conditions.

## 7. Droit applicable
[UE/USA].
""",
}


def body_for(template_id: str) -> str:
    return CONTRACT_BODIES.get(template_id, "")
