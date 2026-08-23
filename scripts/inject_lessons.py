"""
inject_lessons.py — Enrichissement initial des agents ALNUA avant la beta.

Lance-le une fois depuis le dossier ALUNA_HUB :
    python scripts/inject_lessons.py

Chaque leçon est injectée dans Mem0 pour l'agent concerné.
Les agents s'en souviendront lors de leurs prochaines tâches.
"""
import sys
from pathlib import Path

# Charge le .env et le path du repo
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from skills.skill_web_research import teach_agent

# ---------------------------------------------------------------------------
# LEÇONS — format : (agent_id, leçon)
# ---------------------------------------------------------------------------

LESSONS = [

    # ── NUAWAY / dev_app ─────────────────────────────────────────────────
    ("dev_app", (
        "NUAWAY doit fonctionner 100% offline. Le public produit (voyageurs, vanlifers) "
        "est souvent sans réseau. Toutes les données (spots, cartes, favoris) "
        "doivent être accessibles sans connexion. C'est le critère n°1 de l'app."
    )),
    ("dev_app", (
        "Les utilisateurs de Park4Night signalent massivement : interface vieillissante, "
        "spots outdatés sans système de validation communautaire, publicités intrusives "
        "et absence de filtre 'van/camping-car de grande taille'. Ce sont nos axes de différenciation."
    )),
    ("dev_app", (
        "Les utilisateurs NUAWAY utilisent surtout le téléphone pour naviguer. "
        "L'app doit être utilisable avec une seule main, en conduite (commandes vocales à prévoir), "
        "et avec un écran lumineux en plein soleil. UX mobile-first avant tout."
    )),
    ("dev_app", (
        "Les vanlifers voyagent en communauté : les features sociales (partage de spot entre amis, "
        "groupes de voyage, rencontre d'autres van) ont un fort potentiel de rétention. "
        "Signal (app communautaire nomades) a prouvé ce besoin."
    )),
    ("dev_app", (
        "Monétisation NUAWAY la moins rejetée : abonnement annuel unique à prix raisonnable "
        "(< 30€/an). Les pubs et microtransactions sont mal perçues sur ce segment. "
        "Le freemium avec limite de spots sauvegardés est une approche acceptée."
    )),

    # ── NUAWAY / marketing_agent ─────────────────────────────────────────
    ("marketing_agent", (
        "La communauté van life est très active sur Instagram, TikTok et YouTube. "
        "Les contenus qui performent : 'day in the life', spots secrets, tutoriels d'aménagement van. "
        "Les hashtags #vanlife #vanlifers #homeiswhereyouparkit ont des millions d'abonnés."
    )),
    ("marketing_agent", (
        "Le bouche-à-oreille est le canal d'acquisition n°1 dans la communauté nomade. "
        "Une stratégie de referral (partage de spot = 1 mois gratuit) sera plus efficace "
        "que la pub payante pour NUAWAY."
    )),
    ("marketing_agent", (
        "Les utilisateurs de NUAWAY méfient souvent les apps trop 'corporate'. "
        "Positionner le produit sur l'utilité réelle (offline, communauté, confiance), "
        "pas sur le mode de vie de la fondatrice. Emilie (CEO) parle en fondatrice tech "
        "solopreneuse — ton direct et authentique, sans storytelling lifestyle."
    )),

    # ── Naïa / game_director ─────────────────────────────────────────────
    ("game_director", (
        "Les joueurs de No Man's Sky reprochent : génération procédurale trop répétitive après 20h, "
        "manque d'histoire et de sens du but, IA des créatures trop simple. "
        "Naïa doit proposer une IA véritablement émergente et des objectifs narratifs évolutifs."
    )),
    ("game_director", (
        "Minecraft et Valheim prouvent que la boucle core doit être satisfaisante dès les 30 "
        "premières minutes. Naïa a besoin d'un 'first hour experience' fort : arrivée dans le monde, "
        "découverte de Naïa, premier objectif clair. Sans ça, pas de rétention."
    )),
    ("game_director", (
        "Le marché des jeux solo avec IA émergente est quasi-inexistant en 2026. "
        "Naïa se positionne dans un blue ocean si les agents IA sont vraiment perceptibles et uniques. "
        "La différenciation clé : Naïa apprend et se souvient du joueur entre les sessions."
    )),

    # ── Hub / qa_agent ────────────────────────────────────────────────────
    ("qa_agent", (
        "Pour NUAWAY (app mobilité), les tests doivent inclure : mode avion (offline), "
        "GPS sans données, batterie faible, connexion instable (2G). "
        "Les bugs en conditions terrain réelles sont souvent ignorés en dev."
    )),

    # ── Hub / spec_agent ─────────────────────────────────────────────────
    ("spec_agent", (
        "Les specs de NUAWAY doivent toujours inclure un chapitre 'Mode offline'. "
        "Chaque feature doit préciser son comportement sans connexion : "
        "dégradation gracieuse, sync différé, cache local. C'est non négociable."
    )),

    # ── Hub / coo ────────────────────────────────────────────────────────
    ("coo", (
        "ALNUA a plusieurs produits : NUAWAY (app mobilité / voyage, beta), "
        "Naïa (bien-être / monde IA selon branche), Wyrdheim (gaming), Eve (robotique), "
        "Hub IA (agents autonomes). Prioriser selon la roadmap CEO, pas un seul lifestyle."
    )),
    ("coo", (
        "Emilie est CEO solopreneuse. Elle gère tout en solo avec les agents IA. "
        "Ressources limitées : prioriser l'impact, éviter la sur-ingénierie. "
        "Le MVP vaut mieux que le produit parfait. Ne pas cadrer ALNUA comme une marque 'nomade'."
    )),
]

# ---------------------------------------------------------------------------
# Injection
# ---------------------------------------------------------------------------

def main():
    print(f"Injection de {len(LESSONS)} leçons dans Mem0...\n")
    success = 0
    for i, (agent_id, content) in enumerate(LESSONS, 1):
        try:
            teach_agent(agent_id, content, source="Emilie — enrichissement initial beta")
            print(f"✅ [{i:02d}/{len(LESSONS)}] {agent_id} — {content[:60]}…")
            success += 1
        except Exception as e:
            print(f"❌ [{i:02d}/{len(LESSONS)}] {agent_id} — ERREUR: {e}")

    print(f"\n{'='*50}")
    print(f"✅ {success}/{len(LESSONS)} leçons injectées avec succès.")
    if success < len(LESSONS):
        print("⚠️  Vérifie que MEM0_API_KEY est dans ton .env")

if __name__ == "__main__":
    main()
