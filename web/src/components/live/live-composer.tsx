"use client";

import { useState } from "react";
import { Send } from "lucide-react";

import { HubFilePicker } from "@/components/hub/hub-file-picker";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  PASTE_AS_FILE_THRESHOLD,
  shouldConvertPasteToFile,
  uploadHubFile,
} from "@/lib/hub-files-api";
import { wantsClearScreens } from "@/lib/live-clear";
import type { LiveAgentId } from "@/lib/live-api";
import { useLiveStore } from "@/store/live-store";

const EXECUTORS: { id: LiveAgentId; label: string }[] = [
  { id: "secretary", label: "Nadia" },
  { id: "coo", label: "Aria" },
  { id: "plan", label: "Équipe (plan)" },
];

interface Props {
  disabled?: boolean;
  error: string | null;
  onSubmit: (agent: LiveAgentId, instruction: string, fileIds: string[]) => Promise<void>;
}

/** Keyboard fallback: everything the voice session will do also works from here. */
export function LiveComposer({ disabled, error, onSubmit }: Props) {
  const [text, setText] = useState("");
  const [agent, setAgent] = useState<LiveAgentId>("secretary");
  const [sending, setSending] = useState(false);
  const fileIds = useLiveStore((s) => s.composerFileIds);
  const setFileIds = useLiveStore((s) => s.setComposerFileIds);
  const [localError, setLocalError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const instruction = text.trim();
    if (wantsClearScreens(instruction)) {
      useLiveStore.getState().clearScreens();
      setText("");
      return;
    }
    if ((!instruction && fileIds.length === 0) || sending) return;
    setSending(true);
    setLocalError(null);
    try {
      await onSubmit(agent, instruction || "Voir les pièces jointes.", fileIds);
      setText("");
      setFileIds([]);
    } finally {
      setSending(false);
    }
  }

  async function onPaste(e: React.ClipboardEvent<HTMLInputElement>) {
    const pasted = e.clipboardData.getData("text/plain");
    if (!shouldConvertPasteToFile(pasted.length)) return;
    e.preventDefault();
    setLocalError(null);
    try {
      const blob = new File([pasted], `paste-${Date.now()}.txt`, { type: "text/plain" });
      const meta = await uploadHubFile(blob, "live");
      setFileIds(
        fileIds.includes(meta.id) ? fileIds : [...fileIds, meta.id].slice(0, 5),
      );
      setText((prev) => prev.trim() || "Voir le document collé.");
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Collage trop long — upload échoué.");
    }
  }

  const displayError = localError ?? error;

  return (
    <form onSubmit={submit} className="space-y-1.5">
      <HubFilePicker source="live" selectedIds={fileIds} onChange={setFileIds} />
      <div className="flex gap-2">
        <select
          aria-label="Exécutant"
          value={agent}
          onChange={(e) => setAgent(e.target.value as LiveAgentId)}
          className="h-8 rounded-lg border border-input bg-obsidian-2 px-2 text-sm text-ivory"
        >
          {EXECUTORS.map((a) => (
            <option key={a.id} value={a.id}>
              {a.label}
            </option>
          ))}
        </select>
        <Input
          aria-label="Demande"
          placeholder="Demande quelque chose à Nadia…"
          value={text}
          disabled={disabled}
          onChange={(e) => setText(e.target.value)}
          onPaste={onPaste}
          maxLength={4000}
        />
        <Button
          type="submit"
          disabled={disabled || sending || (!text.trim() && fileIds.length === 0)}
        >
          <Send />
          Envoyer
        </Button>
      </div>
      <p className="text-[10px] text-muted-foreground">
        Collage &gt; {PASTE_AS_FILE_THRESHOLD} caractères → fichier (aussi pour la voix).
      </p>
      {displayError && (
        <p role="alert" className="text-xs text-red-400">
          {displayError}
        </p>
      )}
    </form>
  );
}
