# Aria Voss (COO) — assets bureau

## Portrait (statique)
- `office.png` — full-body bureau, utilisé dans OpenRoom / Hub

## Vraie animation — Runway Act-Two uniquement

Les fichiers `*-preview.webm` dans `assets/agents/animations/` sont des **warps procéduraux**
(image qui bouge) — **ne pas** les copier ici.

### Générer les vraies boucles

1. Ajouter `RUNWAYML_API_SECRET` dans `.env`
2. Enregistrer les performances de référence (webcam) :
   ```powershell
   python scripts/record_performance_reference.py --state idle --out assets/agents/aria-voss-idle-reference.mp4
   python scripts/record_performance_reference.py --state working --out assets/agents/aria-voss-working-reference.mp4
   python scripts/record_performance_reference.py --state alert --out assets/agents/aria-voss-alert-reference.mp4
   ```
3. Lancer Act-Two :
   ```powershell
   python scripts/runway_act_two_animate.py --state idle --agent aria-voss --reference assets/agents/aria-voss-idle-reference.mp4 --out web/public/agents/coo/idle-acttwo.webm
   python scripts/runway_act_two_animate.py --state working --agent aria-voss --reference assets/agents/aria-voss-working-reference.mp4 --out web/public/agents/coo/working-acttwo.webm
   python scripts/runway_act_two_animate.py --state alert --agent aria-voss --reference assets/agents/aria-voss-alert-reference.mp4 --out web/public/agents/coo/alert-acttwo.webm
   ```
4. Décommenter `actTwoLoops` dans `web/src/lib/agent-assets.ts`
