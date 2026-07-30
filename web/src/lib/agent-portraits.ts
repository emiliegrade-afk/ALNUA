// FICHIER GÉNÉRÉ — ne pas éditer à la main.
// Régénéré par `node scripts/sync-portraits.mjs` (lancé par predev/prebuild).
// Source : web/public/agents/portraits/

/** Extension du portrait disponible, par id d'agent. Vide = aucun portrait. */
export const AGENT_PORTRAITS: Record<string, string> = {

};

/** URL du portrait d'un agent, ou null s'il n'y en a pas sur disque. */
export function portraitUrl(agentId: string): string | null {
  const ext = AGENT_PORTRAITS[agentId];
  return ext ? `/agents/portraits/${agentId}${ext}` : null;
}
