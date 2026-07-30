/**
 * Identités humaines et exécutives affichées dans le chrome de la console.
 * Centralisées ici plutôt qu'écrites en dur dans le topbar : le nom apparaît
 * à plusieurs endroits (topbar, menu profil) et changer de titulaire ne doit
 * pas demander de chasser des littéraux dans les composants.
 */

/** L'humaine derrière le Hub — carte profil en haut à droite. */
export const HUB_OWNER = {
  /** Sert aussi de clé d'avatar : `/agents/portraits/{id}.png`. */
  id: "owner",
  name: "Emilie Grade",
  role: "Fondatrice & CEO",
} as const;

/** L'agent qui pilote l'exécution — présence permanente à gauche du topbar. */
export const HUB_CHIEF = {
  /** `id` dans `BUREAU_AGENTS` (web/src/lib/agent-bureau.ts). */
  agentId: "coo",
  name: "Aria Voss",
  role: "COO — Chef d'orchestre",
  shortRole: "COO",
} as const;
