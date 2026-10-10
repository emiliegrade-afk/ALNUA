"use client";

import { useState } from "react";
import { Mic, MicOff, Phone, PhoneOff } from "lucide-react";

import type { LiveVoice } from "@/hooks/use-live-voice";
import type { LivePersona } from "@/lib/live-api";
import { portraitUrl } from "@/lib/agent-portraits";
import { cn } from "@/lib/utils";

const PERSONA_AGENT: Record<LivePersona, string> = {
  nadia: "secretary",
  aria: "coo",
};

const PERSONA_NAME: Record<LivePersona, string> = {
  nadia: "Nadia",
  aria: "Aria",
};

const CALL_LABEL: Record<string, string> = {
  idle: "Prête à décrocher",
  error: "Appel interrompu",
  connecting: "Appel en cours…",
  ready: "En ligne",
  listening: "Elle t'écoute",
  thinking: "Elle réfléchit",
  speaking: "Elle parle",
};

export function isInCall(state: string): boolean {
  return state === "ready" || state === "listening" || state === "thinking" || state === "speaking";
}

/** Phone-style stage: portrait + green pick-up / red hang-up (SPEC_JARVIS_LIVE §14). */
export function LiveCallStage({
  voice,
  activeCount,
}: {
  voice: LiveVoice;
  activeCount: number;
}) {
  const [persona, setPersona] = useState<LivePersona>("nadia");
  const inCall = isInCall(voice.state);
  const connecting = voice.state === "connecting";
  const src = portraitUrl(PERSONA_AGENT[persona]);
  const name = PERSONA_NAME[persona];
  const lastLine = [...voice.transcript].reverse().find((l) => l.role === "assistant");

  return (
    <section
      aria-label="Appel"
      className="flex flex-col items-center gap-4 rounded-2xl border border-copper/20 bg-obsidian-2/80 px-4 py-6"
    >
      <div className="relative">
        <span
          className={cn(
            "absolute -inset-3 rounded-full blur-md transition-opacity",
            voice.state === "speaking" && "animate-pulse bg-copper/40",
            voice.state === "listening" && "animate-pulse bg-emerald-400/25",
            voice.state === "thinking" && "bg-copper/20",
            !inCall && "bg-transparent",
          )}
        />
        <div
          className={cn(
            "relative size-52 overflow-hidden rounded-full border-2 shadow-[0_0_40px_rgba(0,0,0,0.45)] sm:size-64",
            voice.state === "speaking" && "border-copper",
            voice.state === "listening" && "border-emerald-400",
            voice.state === "thinking" && "border-copper-dim",
            connecting && "border-copper/50",
            !inCall && !connecting && "border-white/10",
          )}
        >
          {src ? (
            // Portrait file is already sized; next/image is unnecessary here.
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={src}
              alt={name}
              className={cn(
                "size-full object-cover object-top",
                voice.state === "thinking" && "opacity-80",
                connecting && "opacity-60",
              )}
            />
          ) : (
            <div className="flex size-full items-center justify-center bg-obsidian text-3xl text-copper">
              {name.slice(0, 1)}
            </div>
          )}
        </div>
      </div>

      <div className="text-center">
        <p className="text-lg font-medium text-ivory">{name}</p>
        <p className="text-sm text-copper-light" role="status" aria-live="polite">
          {CALL_LABEL[voice.state] ?? CALL_LABEL.idle}
          {activeCount > 0 && ` · ${activeCount} affaire${activeCount > 1 ? "s" : ""} en fond`}
        </p>
        {lastLine && inCall && (
          <p className="mt-2 max-w-md text-sm text-zinc-300">{lastLine.text}</p>
        )}
      </div>

      <div className="flex items-center gap-4">
        {inCall || connecting ? (
          <button
            type="button"
            aria-label="Raccrocher"
            disabled={connecting}
            onClick={voice.disconnect}
            className="flex size-16 items-center justify-center rounded-full bg-red-600 text-white shadow-lg shadow-red-900/40 hover:bg-red-500 disabled:opacity-50"
          >
            <PhoneOff className="size-7" />
          </button>
        ) : (
          <button
            type="button"
            aria-label={`Appeler ${name}`}
            onClick={() => void voice.connect(persona)}
            className="flex size-16 items-center justify-center rounded-full bg-emerald-500 text-white shadow-lg shadow-emerald-900/40 hover:bg-emerald-400"
          >
            <Phone className="size-7" />
          </button>
        )}
        {inCall && (
          <button
            type="button"
            aria-label={voice.muted ? "Réactiver le micro" : "Couper le micro"}
            aria-pressed={voice.muted}
            onClick={voice.toggleMute}
            className={cn(
              "flex size-12 items-center justify-center rounded-full border border-white/15",
              voice.muted ? "bg-zinc-700 text-zinc-300" : "bg-white/5 text-ivory",
            )}
          >
            {voice.muted ? <MicOff className="size-5" /> : <Mic className="size-5" />}
          </button>
        )}
      </div>

      <div className="flex flex-wrap items-center justify-center gap-3 text-xs text-zinc-400">
        <label className="flex items-center gap-1.5">
          Appeler
          <select
            aria-label="Voix de"
            className="h-7 rounded-md border border-white/10 bg-transparent px-1.5"
            value={persona}
            disabled={inCall || connecting}
            onChange={(e) => setPersona(e.target.value as LivePersona)}
          >
            <option value="nadia" className="bg-zinc-900">
              Nadia
            </option>
            <option value="aria" className="bg-zinc-900">
              Aria
            </option>
          </select>
        </label>
        {voice.remainingSeconds !== null && (
          <span>
            {Math.max(0, Math.ceil(voice.remainingSeconds / 60))} min restantes aujourd&apos;hui
          </span>
        )}
      </div>

      {voice.error && (
        <p role="alert" className="max-w-md text-center text-sm text-red-300">
          {voice.error}
        </p>
      )}
    </section>
  );
}
