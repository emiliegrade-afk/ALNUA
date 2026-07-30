// Génère le manifeste des portraits d'agents réellement présents sur disque.
//
// Pourquoi un manifeste plutôt qu'un simple <img onError> : demander un
// fichier absent produit un 404 par avatar affiché. En dev, ces 404 passent
// par le routeur Next, qui compile `/_not-found` et déclenche un bug connu de
// Next 14.2 (« Invariant: missing bootstrap script ») cassant la route
// entière. Le manifeste supprime la requête au lieu de rattraper son échec.
//
// Lancé automatiquement par `predev` et `prebuild` — déposer un PNG puis
// relancer le serveur suffit à le faire apparaître.

import { readdirSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { dirname, join, extname, basename } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const portraitsDir = join(root, "public", "agents", "portraits");
const outFile = join(root, "src", "lib", "agent-portraits.ts");

const VALID = new Set([".png", ".jpg", ".jpeg", ".webp"]);

const ids = existsSync(portraitsDir)
  ? readdirSync(portraitsDir)
      .filter((f) => VALID.has(extname(f).toLowerCase()))
      .map((f) => [basename(f, extname(f)), extname(f).toLowerCase()])
      .sort(([a], [b]) => a.localeCompare(b))
  : [];

const entries = ids.map(([id, ext]) => `  ${JSON.stringify(id)}: ${JSON.stringify(ext)},`);

const content = `// FICHIER GÉNÉRÉ — ne pas éditer à la main.
// Régénéré par \`node scripts/sync-portraits.mjs\` (lancé par predev/prebuild).
// Source : web/public/agents/portraits/

/** Extension du portrait disponible, par id d'agent. Vide = aucun portrait. */
export const AGENT_PORTRAITS: Record<string, string> = {
${entries.join("\n")}
};

/** URL du portrait d'un agent, ou null s'il n'y en a pas sur disque. */
export function portraitUrl(agentId: string): string | null {
  const ext = AGENT_PORTRAITS[agentId];
  return ext ? \`/agents/portraits/\${agentId}\${ext}\` : null;
}
`;

mkdirSync(dirname(outFile), { recursive: true });
writeFileSync(outFile, content, "utf8");
console.log(`[portraits] ${ids.length} portrait(s) détecté(s) → src/lib/agent-portraits.ts`);
