// FICHIER GÉNÉRÉ — ne pas éditer à la main.
// Régénéré par `node scripts/sync-portraits.mjs` (lancé par predev/prebuild).
// Source : web/public/agents/portraits/

/** Extension du portrait disponible, par id d'agent. Vide = aucun portrait. */
export const AGENT_PORTRAITS: Record<string, string> = {
  "accounting": ".png",
  "ads": ".png",
  "ai_programmer": ".png",
  "analyst_business": ".png",
  "analyst_data": ".png",
  "brainstorm": ".png",
  "brand": ".png",
  "coding_coach": ".png",
  "content": ".png",
  "content_app": ".png",
  "content_company": ".png",
  "content_gaming": ".png",
  "content_robo": ".png",
  "controller": ".png",
  "coo": ".png",
  "dev_app": ".png",
  "dev_backend": ".png",
  "dev_frontend": ".png",
  "dev_gaming": ".png",
  "dev_integrator": ".png",
  "electronics": ".png",
  "embedded_dev": ".png",
  "environment_artist": ".png",
  "firmware": ".png",
  "game_director": ".png",
  "hardware": ".png",
  "housekeeper": ".png",
  "industrial_design": ".png",
  "legal_counsel": ".png",
  "level_designer": ".png",
  "marketing": ".png",
  "mechanical": ".png",
  "narrative_designer": ".png",
  "pm": ".png",
  "qa": ".png",
  "qa_gaming": ".png",
  "qa_robot": ".png",
  "rnd_agent": ".png",
  "rnd_ceo": ".png",
  "rnd_committee": ".png",
  "rnd_dossier": ".png",
  "rnd_product": ".png",
  "rnd_social": ".png",
  "rnd_visual": ".png",
  "safety": ".png",
  "secretary": ".png",
  "security_sentinel": ".png",
  "simulation": ".png",
  "sound_designer": ".png",
  "spec": ".png",
  "technical_artist": ".png",
  "vfx_artist": ".png",
  "vision_ai": ".png",
};

/** URL du portrait d'un agent, ou null s'il n'y en a pas sur disque. */
export function portraitUrl(agentId: string): string | null {
  const ext = AGENT_PORTRAITS[agentId];
  return ext ? `/agents/portraits/${agentId}${ext}` : null;
}
