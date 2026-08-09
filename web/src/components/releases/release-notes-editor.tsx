"use client";

import { useState } from "react";
import { Check, Copy, Info } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  APP_STORE_CHAR_LIMIT,
  GOOGLE_PLAY_CHAR_LIMIT,
} from "@/lib/releases-api";
import { cn } from "@/lib/utils";

export type ReleaseNotesTab = "app_store" | "google_play" | "changelog";

interface ReleaseNotesEditorProps {
  tab: ReleaseNotesTab;
  value: string;
  onChange: (value: string) => void;
}

const TAB_CONFIG: Record<
  ReleaseNotesTab,
  { label: string; limit: number | null; hint?: string }
> = {
  app_store: {
    label: "App Store",
    limit: APP_STORE_CHAR_LIMIT,
    hint: "Titre + nouveautés + corrections (max 4000 caractères)",
  },
  google_play: {
    label: "Google Play",
    limit: GOOGLE_PLAY_CHAR_LIMIT,
    hint: "Version condensée (max 500 caractères)",
  },
  changelog: {
    label: "Changelog",
    limit: null,
    hint: "Format Keep a Changelog — ton technique OK",
  },
};

export function ReleaseNotesEditor({
  tab,
  value,
  onChange,
}: ReleaseNotesEditorProps) {
  const [copied, setCopied] = useState(false);
  const config = TAB_CONFIG[tab];
  const count = value.length;
  const overLimit = config.limit !== null && count > config.limit;

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      toast.success("Copié dans le presse-papier");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Impossible de copier");
    }
  }

  return (
    <div className="flex flex-1 flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-titanium">{config.hint}</p>
        <div className="flex items-center gap-2">
          {tab === "app_store" && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="border-copper/20 text-xs text-titanium"
              onClick={() =>
                toast.info(`Limite App Store : ${APP_STORE_CHAR_LIMIT} caractères`)
              }
            >
              <Info className="mr-1.5 h-3.5 w-3.5" />
              Voir la limite (4000 chars)
            </Button>
          )}
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="border-copper/30 text-copper hover:bg-copper/10"
            onClick={handleCopy}
          >
            {copied ? (
              <Check className="mr-1.5 h-3.5 w-3.5" />
            ) : (
              <Copy className="mr-1.5 h-3.5 w-3.5" />
            )}
            Copier
          </Button>
        </div>
      </div>

      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="min-h-[320px] flex-1 resize-y border-copper/20 bg-obsidian-deep/50 font-mono text-sm leading-relaxed text-ivory"
      />

      {config.limit !== null && (
        <p
          className={cn(
            "text-right text-xs",
            overLimit ? "font-medium text-red-400" : "text-titanium"
          )}
        >
          {count} / {config.limit} caractères
        </p>
      )}
    </div>
  );
}

interface ReleaseNotesTabsProps {
  activeTab: ReleaseNotesTab;
  onTabChange: (tab: ReleaseNotesTab) => void;
}

export function ReleaseNotesTabs({
  activeTab,
  onTabChange,
}: ReleaseNotesTabsProps) {
  const tabs: ReleaseNotesTab[] = ["app_store", "google_play", "changelog"];

  return (
    <div className="flex gap-1 rounded-lg border border-copper/15 bg-obsidian-deep/50 p-1">
      {tabs.map((tab) => (
        <button
          key={tab}
          type="button"
          onClick={() => onTabChange(tab)}
          className={cn(
            "flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors",
            activeTab === tab
              ? "bg-copper/15 text-copper-glow"
              : "text-titanium hover:text-ivory"
          )}
        >
          {TAB_CONFIG[tab].label}
        </button>
      ))}
    </div>
  );
}
