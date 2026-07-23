"use client";

import { useEffect, useRef } from "react";
import { Loader2, Play, Terminal, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { IdeLiveTask } from "@/lib/ide-api";

export type BottomPanelTab = "terminal" | "output" | "agent";

export function IdeBottomPanel({
  open,
  tab,
  workspace,
  terminalCmd,
  terminalHistory,
  liveTasks,
  diff,
  onTabChange,
  onClose,
  onCmdChange,
  onRun,
  running,
}: {
  open: boolean;
  tab: BottomPanelTab;
  workspace: string;
  terminalCmd: string;
  terminalHistory: Array<{ cmd: string; output: string; exitCode: number }>;
  liveTasks: IdeLiveTask[];
  diff: string;
  onTabChange: (tab: BottomPanelTab) => void;
  onClose: () => void;
  onCmdChange: (cmd: string) => void;
  onRun: () => void;
  running: boolean;
}) {
  const endRef = useRef<HTMLDivElement>(null);
  const activeTask = liveTasks[0];

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [terminalHistory, activeTask?.log]);

  if (!open) return null;

  const tabs: Array<{ id: BottomPanelTab; label: string }> = [
    { id: "terminal", label: "Terminal" },
    { id: "output", label: "Sortie" },
    { id: "agent", label: "Agent" },
  ];

  return (
    <div className="flex min-h-0 shrink-0 flex-col border-t border-bronze-faint bg-obsidian-deep">
      <div className="flex shrink-0 items-center border-b border-bronze-faint">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => onTabChange(t.id)}
            className={cn(
              "border-r border-bronze-faint px-3 py-1.5 font-mono text-[10px] uppercase tracking-wider transition-colors",
              tab === t.id
                ? "bg-obsidian text-bronze-bright"
                : "text-titane/50 hover:text-ivoire",
            )}
          >
            {t.label}
          </button>
        ))}
        <div className="ml-auto flex items-center gap-1 pr-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-titane/50 hover:text-ivoire"
            aria-label="Fermer le panneau"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-hidden">
        {tab === "terminal" ? (
          <div className="flex h-full flex-col p-2">
            <div className="flex shrink-0 gap-2">
              <div className="flex items-center gap-1 font-mono text-[10px] text-titane/45">
                <Terminal className="h-3 w-3" />
                sandbox
              </div>
              <input
                value={terminalCmd}
                onChange={(e) => onCmdChange(e.target.value)}
                disabled={workspace !== "sandbox" || running}
                className="min-w-0 flex-1 rounded border border-bronze-faint bg-obsidian px-2 py-1 font-mono text-xs text-ivoire outline-none focus:border-bronze/40 disabled:opacity-50"
                placeholder={
                  workspace === "sandbox"
                    ? "python hello.py"
                    : "Terminal réservé au bac à sable"
                }
                onKeyDown={(e) => e.key === "Enter" && onRun()}
              />
              <Button
                type="button"
                size="sm"
                className="h-7 gap-1 px-2 text-xs"
                disabled={workspace !== "sandbox" || running}
                onClick={onRun}
              >
                {running ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <Play className="h-3 w-3" />
                )}
                Run
              </Button>
            </div>
            <pre className="mt-2 min-h-0 flex-1 overflow-auto rounded bg-obsidian p-2 font-mono text-[11px] leading-relaxed text-titane/80">
              {terminalHistory.length === 0
                ? "$ python / pytest / node …"
                : terminalHistory.map((h, i) => (
                    <span key={i}>
                      <span className="text-bronze/80">$ {h.cmd}</span>
                      {"\n"}
                      {h.output}
                      {h.exitCode !== 0 ? (
                        <span className="text-red-400/80">
                          {"\n"}[exit {h.exitCode}]
                        </span>
                      ) : null}
                      {"\n\n"}
                    </span>
                  ))}
              <div ref={endRef} />
            </pre>
          </div>
        ) : null}

        {tab === "output" ? (
          <pre className="h-full overflow-auto p-3 font-mono text-[11px] text-titane/75">
            {diff.trim() || "Aucun diff git pour ce workspace."}
          </pre>
        ) : null}

        {tab === "agent" ? (
          <div className="flex h-full flex-col gap-2 overflow-auto p-2">
            {activeTask ? (
              <>
                <p className="font-mono text-[10px] text-emerald-300/90">
                  Théo · #{activeTask.issue_number} · {activeTask.title} ·{" "}
                  {activeTask.progress ?? 0}%
                </p>
                <pre className="flex-1 overflow-auto rounded bg-obsidian p-2 font-mono text-[10px] leading-relaxed text-emerald-400/85">
                  {(activeTask.log ?? []).join("\n") || "En cours…"}
                </pre>
                {(activeTask.recent_code ?? []).length > 0 ? (
                  <pre className="max-h-28 overflow-auto rounded border border-bronze-faint p-2 font-mono text-[10px] text-bronze/80">
                    {(activeTask.recent_code ?? []).join("\n")}
                  </pre>
                ) : null}
              </>
            ) : (
              <p className="p-4 text-center text-sm text-titane/50">
                Aucun agent en train de coder
              </p>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
}
