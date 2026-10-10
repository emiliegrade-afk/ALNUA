"use client";

import { cn } from "@/lib/utils";
import type { VoiceState } from "@/lib/live-realtime";
import type { LiveConnection } from "@/store/live-store";

export type OrbState =
  | "offline"
  | "idle"
  | "working"
  | "connecting"
  | "listening"
  | "thinking"
  | "speaking";

/** A live voice session wins over the task feed: it is what the user is looking at. */
export function orbState(
  connection: LiveConnection,
  activeCount: number,
  voice: VoiceState = "idle",
): OrbState {
  if (voice === "connecting") return "connecting";
  if (voice === "listening" || voice === "thinking" || voice === "speaking") return voice;
  if (connection !== "online") return "offline";
  return activeCount > 0 ? "working" : "idle";
}

const LABELS: Record<OrbState, string> = {
  offline: "Hors ligne — reconnexion…",
  idle: "Nadia est disponible",
  working: "Nadia travaille",
  connecting: "Connexion à Nadia…",
  listening: "Nadia t'écoute",
  thinking: "Nadia réfléchit",
  speaking: "Nadia parle",
};

const HALO: Record<OrbState, string> = {
  offline: "bg-zinc-600/20",
  idle: "bg-copper/15",
  working: "animate-ping bg-copper/40",
  connecting: "animate-pulse bg-copper/30",
  listening: "animate-ping bg-emerald-400/40",
  thinking: "animate-pulse bg-copper/40",
  speaking: "animate-ping bg-copper/50",
};

const CORE: Record<OrbState, string> = {
  offline: "bg-zinc-600",
  idle: "bg-copper-dim shadow-[0_0_12px_2px_rgba(184,110,69,0.4)]",
  working: "bg-copper shadow-[0_0_18px_4px_rgba(224,155,106,0.55)]",
  connecting: "bg-copper-dim",
  listening: "bg-emerald-400 shadow-[0_0_18px_4px_rgba(52,211,153,0.5)]",
  thinking: "bg-copper shadow-[0_0_14px_3px_rgba(224,155,106,0.45)]",
  speaking: "bg-copper-light shadow-[0_0_22px_6px_rgba(224,155,106,0.6)]",
};

/** Presence indicator that follows the real voice session and the task feed. */
export function NadiaOrb({ state, activeCount }: { state: OrbState; activeCount: number }) {
  return (
    <div className="flex items-center gap-3" role="status" aria-live="polite">
      <span className="relative flex size-10 items-center justify-center">
        <span className={cn("absolute inset-0 rounded-full", HALO[state])} />
        <span className={cn("relative size-5 rounded-full", CORE[state])} />
      </span>
      <div className="leading-tight">
        <p className="text-sm font-medium text-ivory">{LABELS[state]}</p>
        {activeCount > 0 && (
          <p className="text-xs text-copper-light">
            {activeCount} tâche{activeCount > 1 ? "s" : ""} en cours
          </p>
        )}
      </div>
    </div>
  );
}
