"use client";

import { useState } from "react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import { RefreshCw, Server, X } from "lucide-react";
import {
  useHubHealthLive,
} from "@/hooks/use-hub-health-live";
import type { ApiHealthStatus } from "@/lib/hub-health";
import { cn } from "@/lib/utils";

const PHASE_COPY = {
  checking: {
    label: "Vérification…",
    detail: "Connexion au serveur Hub en cours.",
  },
  ok: {
    label: "Hub connecté",
    detail: "API en ligne · clé Hub OK · agents joignables.",
  },
  key: {
    label: "Clé API",
    detail:
      "Le serveur répond mais la clé Hub manque côté Next.js. Ajoute HUB_API_KEY dans web/.env.local puis redémarre npm run dev.",
  },
  down: {
    label: "Hub arrêté",
    detail:
      "Le serveur ne répond pas. Double-clic Relancer Hub.bat puis Ctrl+F5.",
  },
} as const;

function downCopy(status: ApiHealthStatus | null): { label: string; detail: string } {
  if (status?.layer === "api") {
    return {
      label: "API Hub lente",
      detail:
        "L'interface tourne mais l'API met du temps a repondre (agents en cours). Patiente ou relance Relancer Hub.bat.",
    };
  }
  if (status?.layer === "web") {
    return {
      label: "Interface arrêtée",
      detail:
        "Next.js n'est pas joignable. Lance Relancer Hub.bat et attends ~30 s.",
    };
  }
  return PHASE_COPY.down;
}

export function HubStatusMonitor() {
  const { phase, status, lastCheckedAt, refresh } = useHubHealthLive();
  const [expanded, setExpanded] = useState(false);

  const copy =
    phase === "down" ? downCopy(status) : PHASE_COPY[phase];
  const showAlert = phase === "down" || phase === "key";

  return (
    <>
      {showAlert && expanded ? (
        <button
          type="button"
          className="fixed inset-0 z-[55] bg-obsidian/80 backdrop-blur-[1px]"
          aria-label="Fermer le détail"
          onClick={() => setExpanded(false)}
        />
      ) : null}

      <div
        className={cn(
          "fixed z-[60] flex flex-col items-end gap-2",
          "top-4 right-4 sm:top-5 sm:right-5"
        )}
      >
        {expanded ? (
          <div
            className={cn(
              "w-[min(92vw,20rem)] rounded-xl border p-4 shadow-2xl backdrop-blur-md",
              phase === "ok" && "border-emerald-500/30 bg-obsidian-2/95",
              phase === "checking" && "border-white/15 bg-obsidian-2/95",
              phase === "key" && "border-amber-500/35 bg-amber-950/40",
              phase === "down" && "border-red-500/40 bg-red-950/50"
            )}
          >
            <div className="mb-2 flex items-start justify-between gap-2">
              <div className="flex items-center gap-2">
                <Server className="h-4 w-4 shrink-0 text-copper" />
                <p className="font-title text-sm text-ivory">Monitoring Hub</p>
              </div>
              <button
                type="button"
                onClick={() => setExpanded(false)}
                className="rounded p-1 text-titanium/60 hover:bg-white/5 hover:text-ivory"
                aria-label="Fermer"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <p className="text-sm font-medium text-ivory">{copy.label}</p>
            <p className="mt-2 text-xs leading-relaxed text-titanium/80">
              {copy.detail}
            </p>
            {lastCheckedAt ? (
              <p className="mt-3 text-[10px] text-titanium/50">
                Dernière vérif.{" "}
                {format(lastCheckedAt, "HH:mm:ss", { locale: fr })}
              </p>
            ) : null}
            <button
              type="button"
              onClick={() => refresh()}
              className="mt-3 flex items-center gap-1.5 rounded-lg border border-white/10 px-2.5 py-1.5 text-xs text-titanium hover:bg-white/5 hover:text-ivory"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Revérifier
            </button>
          </div>
        ) : null}

        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className={cn(
            "flex items-center gap-2 rounded-full border px-3 py-2 shadow-lg backdrop-blur-md transition",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-copper/50",
            phase === "ok" &&
              "border-emerald-500/35 bg-obsidian-2/90 hover:border-emerald-500/55",
            phase === "checking" &&
              "border-white/15 bg-obsidian-2/90 hover:border-white/25",
            phase === "key" &&
              "border-amber-500/45 bg-amber-950/60 hover:border-amber-400/60 animate-pulse",
            phase === "down" &&
              "border-red-500/50 bg-red-950/70 hover:border-red-400/70 animate-pulse"
          )}
          title={copy.detail}
          aria-live="polite"
          aria-label={`Statut Hub : ${copy.label}`}
        >
          <span className="relative flex h-2.5 w-2.5 shrink-0">
            {phase === "ok" ? (
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-50" />
            ) : null}
            {phase === "down" ? (
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-60" />
            ) : null}
            <span
              className={cn(
                "relative inline-flex h-2.5 w-2.5 rounded-full",
                phase === "ok" && "bg-emerald-500 hub-status-glow-ok",
                phase === "checking" && "bg-titanium/50",
                phase === "key" && "bg-amber-400",
                phase === "down" && "bg-red-500"
              )}
            />
          </span>
          <span
            className={cn(
              "font-body text-xs font-medium",
              phase === "ok" && "text-emerald-300",
              phase === "checking" && "text-titanium/80",
              phase === "key" && "text-amber-200",
              phase === "down" && "text-red-200"
            )}
          >
            {copy.label}
          </span>
        </button>
      </div>

      {showAlert && !expanded ? (
        <div
          className={cn(
            "pointer-events-none fixed left-0 right-0 top-0 z-[54] border-b px-4 py-2 text-center text-xs font-medium backdrop-blur-sm",
            phase === "down" && "border-red-500/30 bg-red-950/80 text-red-200",
            phase === "key" && "border-amber-500/30 bg-amber-950/80 text-amber-100"
          )}
          role="status"
        >
          {phase === "down"
            ? `☕ ${downCopy(status).label} — relance Relancer Hub.bat`
            : "⚠️ Clé API Hub manquante — voir web/.env.local"}
        </div>
      ) : null}
    </>
  );
}
