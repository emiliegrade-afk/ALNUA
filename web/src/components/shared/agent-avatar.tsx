"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { portraitUrl } from "@/lib/agent-portraits";
import type { AgentStatus } from "@/lib/openroom-api";

type Status = AgentStatus["status"];

export const AVATAR_STATUS_DOT: Record<Status, string> = {
  idle: "bg-titane/40",
  working: "bg-bronze-bright",
  waiting: "bg-glow",
  error: "bg-red-400",
};

/**
 * Teintes déterministes tirées de la charte uniquement (obsidienne / cuivre /
 * titane) — quatre variantes suffisent à différencier les agents d'un même
 * bureau sans introduire une couleur hors palette.
 */
const TINTS = [
  { ring: "#E09B6A", base: "#2A1C10" },
  { ring: "#F0C4A0", base: "#2E2015" },
  { ring: "#A7ADB5", base: "#1C1F22" },
  { ring: "#B86E45", base: "#241708" },
] as const;

function tintFor(seed: string) {
  let h = 0;
  for (let i = 0; i < seed.length; i += 1) h = (h * 31 + seed.charCodeAt(i)) >>> 0;
  return TINTS[h % TINTS.length];
}

function initialsOf(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

interface AgentAvatarProps {
  agentId: string;
  name: string;
  /** Diamètre en px. */
  size?: number;
  status?: Status;
  /** Anneau cuivre autour du disque (cartes mises en avant). */
  ring?: boolean;
  className?: string;
}

/**
 * Portrait d'agent — affiche le fichier de `public/agents/portraits/` quand il
 * existe, sinon un monogramme obsidienne/cuivre de même diamètre, même anneau
 * et même pastille de statut.
 *
 * La présence du fichier est connue via le manifeste généré
 * (`scripts/sync-portraits.mjs`) et non testée à l'exécution : demander un
 * fichier absent produit un 404 par avatar, et en dev ces 404 font compiler
 * `/_not-found`, ce qui déclenchait un bug Next 14.2 (« Invariant: missing
 * bootstrap script ») qui casse la page entière. On ne demande donc que ce qui
 * existe. Déposer un PNG puis relancer le serveur suffit à le faire
 * apparaître.
 */
export function AgentAvatar({
  agentId,
  name,
  size = 40,
  status,
  ring = false,
  className,
}: AgentAvatarProps) {
  const src = portraitUrl(agentId);
  // Le fichier peut disparaître entre deux générations du manifeste — on garde
  // un repli, mais il ne s'active plus dans le cas nominal « aucun portrait ».
  const [failed, setFailed] = useState(false);
  const tint = tintFor(agentId);
  const dotSize = Math.max(8, Math.round(size * 0.26));

  return (
    <span
      className={cn("relative inline-flex shrink-0", className)}
      style={{ width: size, height: size }}
    >
      <span
        className="flex h-full w-full items-center justify-center overflow-hidden rounded-full"
        style={{
          background: `radial-gradient(circle at 30% 25%, ${tint.base}, #080808 78%)`,
          boxShadow: ring
            ? `0 0 0 2px ${tint.ring}, 0 0 12px -2px ${tint.ring}66`
            : `inset 0 0 0 1px ${tint.ring}55`,
        }}
      >
        {src && !failed ? (
          // `img` et non `next/image` : le portrait est déjà dimensionné et
          // servi en statique, l'optimiseur n'apporte rien et traite un
          // fichier manquant comme une erreur bloquante.
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={src}
            alt=""
            width={size}
            height={size}
            className="h-full w-full object-cover"
            onError={() => setFailed(true)}
          />
        ) : (
          <span
            className="font-title font-semibold leading-none tracking-wide"
            style={{ color: tint.ring, fontSize: Math.max(9, Math.round(size * 0.36)) }}
          >
            {initialsOf(name)}
          </span>
        )}
      </span>

      {status ? (
        <span
          className={cn(
            "absolute bottom-0 right-0 rounded-full border-2 border-obsidian-deep",
            AVATAR_STATUS_DOT[status]
          )}
          style={{ width: dotSize, height: dotSize }}
        />
      ) : null}
    </span>
  );
}
