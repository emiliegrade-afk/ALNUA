"use client";

import type { LiveVoice } from "@/hooks/use-live-voice";

/** Captions under the call — what was heard and said. */
export function LiveVoiceControls({ voice }: { voice: LiveVoice }) {
  if (voice.transcript.length === 0) return null;

  return (
    <ul className="space-y-1 text-sm text-zinc-300" aria-label="Transcription">
      {voice.transcript.map((line, i) => (
        <li key={i} className={line.role === "user" ? "text-zinc-400" : "text-ivory"}>
          <span className="mr-1 text-xs uppercase text-copper-light">
            {line.role === "user" ? "Toi" : "Nadia"}
          </span>
          {line.text}
        </li>
      ))}
    </ul>
  );
}
