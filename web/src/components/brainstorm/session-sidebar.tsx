"use client";

import { format, formatDistanceToNow } from "date-fns";
import { fr } from "date-fns/locale";
import { ChevronRight, FileText, History, Loader2, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { BrainstormSession } from "@/lib/brainstorm";
import { cn } from "@/lib/utils";

interface SessionSidebarProps {
  sessions: BrainstormSession[];
  activeSessionId: string | null;
  collapsed: boolean;
  onToggle: () => void;
  onSelect: (sessionId: string) => void;
  onNewSession: () => void;
  onSummarize?: (sessionId: string) => void;
  summarizingId?: string | null;
  loading?: boolean;
}

export function SessionSidebar({
  sessions,
  activeSessionId,
  collapsed,
  onToggle,
  onSelect,
  onNewSession,
  onSummarize,
  summarizingId,
  loading,
}: SessionSidebarProps) {
  if (collapsed) {
    return (
      <div className="flex shrink-0 flex-col border-l border-white/[0.06] bg-sidebar/60">
        <button
          type="button"
          onClick={onToggle}
          className="flex h-full min-h-[120px] w-12 flex-col items-center justify-start gap-2 border-0 bg-transparent px-2 py-4 text-copper transition hover:bg-copper/10"
          aria-label="Ouvrir l'historique des sessions"
        >
          <History className="h-4 w-4" />
          <span className="text-[10px] uppercase tracking-wider text-titanium [writing-mode:vertical-rl]">
            Sessions
          </span>
        </button>
      </div>
    );
  }

  return (
    <aside className="flex min-h-0 w-72 shrink-0 flex-col border-l border-white/[0.06] bg-sidebar/60">
      <div className="flex shrink-0 items-center justify-between border-b border-white/[0.06] px-4 py-3">
        <div className="flex items-center gap-2 text-sm text-ivory/75">
          <History className="h-4 w-4 text-copper" />
          Sessions
        </div>
        <button
          type="button"
          onClick={onToggle}
          className="rounded p-1 text-titanium hover:bg-white/[0.04] hover:text-ivory/75"
          aria-label="Replier l'historique"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>

      <div className="shrink-0 p-3">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={onNewSession}
          className="w-full border-copper/25 bg-copper/5 text-copper-glow hover:bg-copper/15 hover:text-copper-glow"
        >
          <Plus className="mr-1.5 h-3.5 w-3.5" />
          Nouvelle session
        </Button>
      </div>

      <ScrollArea className="min-h-0 flex-1 px-2 pb-4">
        {loading ? (
          <p className="px-2 py-4 text-center text-xs text-titanium/60">
            Chargement…
          </p>
        ) : sessions.length === 0 ? (
          <p className="px-2 py-4 text-center text-xs text-titanium/60">
            Aucune session passée
          </p>
        ) : (
          <ul className="space-y-1">
            {sessions.map((s) => {
              const isSummarizing = summarizingId === s.session_id;
              return (
                <li key={s.session_id} className="group relative">
                  <button
                    type="button"
                    onClick={() => onSelect(s.session_id)}
                    aria-current={
                      activeSessionId === s.session_id ? "true" : undefined
                    }
                    className={cn(
                      "w-full rounded-lg px-3 py-2.5 text-left transition",
                      activeSessionId === s.session_id
                        ? "bg-copper/15 ring-1 ring-copper/25"
                        : "hover:bg-white/[0.03]"
                    )}
                  >
                    {s.has_summary && s.summary_title ? (
                      <div className="flex items-start gap-1.5">
                        <FileText className="mt-0.5 h-3 w-3 shrink-0 text-naia-glow" />
                        <p className="line-clamp-2 text-xs font-medium text-ivory/90">
                          {s.summary_title}
                        </p>
                      </div>
                    ) : (
                      <p className="line-clamp-2 text-xs italic text-titanium/70">
                        Session du{" "}
                        {format(new Date(s.created_at), "d MMM yyyy", {
                          locale: fr,
                        })}
                      </p>
                    )}

                    <div className="mt-1 flex items-center justify-between text-[10px] text-titanium/60">
                      <span>{s.project_name ?? "ALNUA Global"}</span>
                      <span>
                        {formatDistanceToNow(new Date(s.updated_at), {
                          addSuffix: true,
                          locale: fr,
                        })}
                      </span>
                    </div>
                    {s.message_count > 0 && (
                      <p className="mt-0.5 text-[10px] text-copper/60">
                        {s.message_count} échange
                        {s.message_count > 1 ? "s" : ""}
                        {s.summary_number != null && (
                          <span className="text-titanium/50">
                            {" "}
                            · Fiche #{String(s.summary_number).padStart(3, "0")}
                          </span>
                        )}
                      </p>
                    )}
                  </button>

                  {onSummarize && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSummarize(s.session_id);
                      }}
                      disabled={isSummarizing}
                      className={cn(
                        "absolute right-2 top-2 rounded-md border border-white/[0.08] bg-obsidian/90 px-1.5 py-0.5 text-[10px] text-titanium opacity-0 transition group-hover:opacity-100 hover:border-copper/30 hover:text-copper-glow",
                        isSummarizing && "opacity-100"
                      )}
                      title="Générer ou voir le compte-rendu"
                    >
                      {isSummarizing ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      ) : (
                        <>📄 Compte-rendu</>
                      )}
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </ScrollArea>
    </aside>
  );
}
