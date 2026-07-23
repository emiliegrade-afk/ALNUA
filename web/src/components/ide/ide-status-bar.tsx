"use client";

import { Circle, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function IdeStatusBar({
  workspaceLabel,
  filePath,
  language,
  line,
  col,
  dirty,
  readOnly,
  apiOnline,
  saving,
  onSave,
}: {
  workspaceLabel: string;
  filePath: string | null;
  language: string;
  line: number;
  col: number;
  dirty: boolean;
  readOnly: boolean;
  apiOnline: boolean;
  saving: boolean;
  onSave: () => void;
}) {
  return (
    <footer className="flex h-[22px] shrink-0 items-center justify-between border-t border-bronze-faint bg-bronze/8 px-2 font-mono text-[10px] text-titane/70">
      <div className="flex min-w-0 items-center gap-3">
        <span className="truncate text-titane/55">{workspaceLabel}</span>
        {filePath ? (
          <span className="hidden truncate text-titane/45 sm:inline">{filePath}</span>
        ) : null}
        <span
          className={cn(
            "inline-flex items-center gap-1",
            apiOnline ? "text-emerald-400/80" : "text-red-400/80",
          )}
        >
          <Circle className="h-1.5 w-1.5 fill-current" />
          API
        </span>
      </div>
      <div className="flex items-center gap-3">
        {dirty && !readOnly ? (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-5 gap-1 px-1.5 text-[10px] text-bronze-bright hover:text-bronze-bright"
            disabled={saving}
            onClick={onSave}
          >
            <Save className="h-3 w-3" />
            {saving ? "…" : "Ctrl+S"}
          </Button>
        ) : null}
        {filePath ? (
          <>
            <span className="text-titane/50">{language}</span>
            <span>
              Ln {line}, Col {col}
            </span>
            {readOnly ? (
              <span className="text-amber-300/80">lecture seule</span>
            ) : null}
          </>
        ) : null}
      </div>
    </footer>
  );
}
