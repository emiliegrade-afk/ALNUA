# SPEC — Overlay Jarvis (Nadia / Aria)

> Contrat produit Lot 0 : **faits en texte**, **réplique en voix**.
> Persona Nadia / Aria **inchangé** pour l’instant — on recale le ton après
> avoir vu comment elle agit (Lots 1+).
>
> **Statut :** Lot 0 validé 2026-08-14 · **implémentation :** Phase 47
> **Décision :** DEC-033.

---

## 1. Objectif

Emilie parle (texte ou vocal). Nadia ou Aria **agit**. Elle reçoit :

1. **Texte** = les faits (créneaux, brouillon, statut pipeline).
2. **Voix** = 1–2 phrases *sur* ces faits, sans les relire.

Ce n’est pas un clone Marvel, pas un graphe n8n, pas un bot unique « Jarvis ».

| Rôle | Canal | Voix |
|------|--------|------|
| **Nadia** | Telegram secrétaire + ALNUA Desk | Quasi chaque réponse utile |
| **Aria** | Telegram COO | Seulement alerte / fin d’action / décision |

---

## 2. Décisions Lot 0 (2026-08-14)

| Axe | Décision |
|-----|----------|
| Persona files | **Pas touchés** (`personas_direction`, operating spec). Recalage après Lot 1. |
| Split canaux | Texte = faits. Voix = overlay. Jamais l’inverse. |
| Tutoiement | Toujours. Jamais « sir », jamais butler Marvel. |
| TTS v1 | **Edge TTS** (déjà Desk). ElevenLabs = Lot 5 si la voix Edge ne suffit pas. |
| Orchestration | Métier Python Hub. n8n = trigger seulement (règle `async-jobs`). |
| Flag | `TELEGRAM_VOICE_REPLIES=0` par défaut ; on allume pour tester. |
| Échec voix | Le texte part quand même. Overlay / TTS / STT ne cassent jamais la réponse. |
| Langue | Français. Overlay ≤ ~200 caractères. |

---

## 3. Règles overlay (à coller dans le prompt Lot 1)

**Interdit de dire à voix haute :** emails, numéros, heures précises en liste,
corps de mail, JSON, URLs.

**Autorisé :** une réaction, une priorité, une prochaine étape.

**Nadia (quotidien) :** sèche, compétente, tutoiement. Vanne légère OK si ça
n’écrase pas l’info. Pas de « sir ».

**Aria (ops) :** directe, COO. Pas de blague si le pipeline est cassé ou un
agent a échoué. Silence vocal si c’est juste une question d’état
(« c’est quoi le pipeline » → texte only).

Si l’overlay échoue ou recopie des faits → **pas d’audio**.

---

## 4. Cinq exemples (gold Lot 1)

Ces paires sont la référence des tests. Le persona conversation actuelle peut
rester « pro / chaleureux » : l’overlay est un **second passage**.

### 4.1 Agenda (Nadia)

**Faits (texte) :**
```
12h30 — déjeuner Camille
15h — bloc R&D
2 mails urgents (Jules, Solène)
```

**Voix :** `Journée dense. Je te laisse le bloc R&D — je m’occupe de Camille et des deux mails.`

**Mauvais :** relire 12h30 / 15h / les noms en liste.

### 4.2 Mail (Nadia)

**Faits (texte) :** brouillon à Jules, objet « Facture août », 3 paragraphes visibles à l’écran.

**Voix :** `Brouillon prêt pour Jules. Tu valides, j’envoie.`

**Mauvais :** dicter l’objet ou le corps.

### 4.3 Contact (Nadia)

**Faits (texte) :** `Camille Rousseau — camille@alnua.dev — +33 6 12 34 56 78`

**Voix :** `Je te l’affiche. Dis-moi si je dois lui écrire.`

**Mauvais :** épeler l’email ou le numéro.

### 4.4 Météo / web (Nadia)

**Faits (texte) :** `San Francisco — 18 °C, ciel dégagé, pas de pluie.`

**Voix :** `Beau temps. Pas besoin de parapluie.`

**Mauvais :** réciter la température et chaque condition.

*(L’intent météo/web en tool du matin = Lot 3. L’overlay, lui, est déjà défini.)*

### 4.5 Relance Théo (Aria)

**Faits (texte) :** `Théo bloqué sur le merge Hub. Pipeline Academy : 2 PRs ouvertes.`

**Voix :** `Je relance Théo sur le merge. Toi tu regardes les deux PRs si tu veux.`

**Mauvais :** une vanne sur le blocage. Question d’état sans action → **pas d’audio**.

---

## 5. Lots suivants (pas Lot 0)

| Lot | Contenu | Dépend |
|-----|---------|--------|
| **1** | Telegram Nadia : STT Whisper + overlay + Edge TTS + `filters.VOICE` | ce contrat |
| **2** | ALNUA Desk : même overlay (ne plus lire le pavé) ; repli sans LLM | Lot 1 |
| **3** | Brief 8h + overlay ; research/météo comme tool | Lot 1 |
| **4** | Aria : STT oui ; TTS seulement alerte / action / décision | Lot 1 |
| **5** | ElevenLabs optionnel (2 voice_id originaux, fallback Edge) | si Edge ne suffit pas |
| **Persona** | Recalage Nadia « copine / secrétaire » | **après** avoir vu Lots 1+ |

Fichiers Lot 1 : `services/voice_overlay.py`, `services/telegram_voice.py`,
`bots/telegram_secretary_voice.py`, flag `TELEGRAM_VOICE_REPLIES`.

---

## 6. Hors scope

- Voix Jarvis Marvel / clone ElevenLabs « movie »
- Workflow n8n recopié de la vidéo Zubair
- Un seul bot Jarvis
- Retell / téléphone
- Réécriture `config/personas_direction.py` / operating spec secretary

---

## 7. Done Lot 0

- [x] Split faits / voix figé
- [x] 5 exemples gold
- [x] TTS v1 = Edge
- [x] Persona reporté volontairement
- [x] DEC-033 + Phase 47 ROADMAP

## 8. Done Lot 1

- [x] Telegram Nadia `filters.VOICE` + Whisper STT
- [x] Overlay LLM (faits / réplique) + drop si fuite
- [x] Edge TTS après le texte ; échec audio ≠ échec texte
- [x] Flag `TELEGRAM_VOICE_REPLIES` off par défaut
- [x] Tests gold + mocks STT/TTS

## 9. Done Lot 2

- [x] Desk : TTS = overlay, pas le pavé à l'écran
- [x] Stop TTS dès qu'Emilie renvoie un message
- [x] Repli local sans LLM (`VOICE_OVERLAY_LLM=0`) — pas de modèle open source sur le PC
- [x] Edge TTS inchangé (cloud Microsoft, gratuit)

## 10. Done Lot 3

- [x] Brief 8h : texte inchangé + overlay vocal (bot Nadia et notify Hub)
- [x] Météo en tool (`wttr.in`, pas d'OpenRouter, pas de LLM local)
- [x] Recherche déjà tool ; overlay local si crédits à sec
- [x] Repli mots-clés si le classifieur LLM est down (météo / brief / recherche)
- [x] Overlay météo gold : « Beau temps. Pas besoin de parapluie. » (sans réciter °C)

## 11. Done Lot 4

- [x] Telegram Aria `filters.VOICE` + Whisper STT (bot COO, séparé de Nadia)
- [x] TTS overlay seulement alerte / action / décision (`should_speak_overlay` COO)
- [x] Question d'état (« c'est quoi le pipeline ») → texte only, pas d'audio
- [x] Même flag `TELEGRAM_VOICE_REPLIES` ; échec voix ≠ échec texte
