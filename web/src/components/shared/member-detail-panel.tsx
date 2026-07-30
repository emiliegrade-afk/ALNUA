"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Sparkline } from "@/components/console/charts";
import { fetchCostReport } from "@/lib/admin-costs-api";
import { fetchLibraryTopics, type LibraryTopic } from "@/lib/library-api";
import type { AgentStatus } from "@/lib/openroom-api";
import { cn } from "@/lib/utils";

interface MemberDetailPanelProps {
  agent: { id: string; name: string; icon?: string; role: string; skills: string[] };
  /** Bureau du département affiché — filtre l'onglet Mémoire sur ses sujets appris. */
  bureau: string;
  status: AgentStatus;
  onClose: () => void;
}

const STATUS_LABEL: Record<AgentStatus["status"], string> = {
  idle: "Veille",
  working: "En train de coder...",
  waiting: "En attente...",
  error: "Erreur",
};

type SubTab = "apercu" | "competences" | "performance" | "memoire";

/**
 * Extends AgentFocusPanel's idea (avatar + status + task) into a full member
 * profile for the Département workspace's Équipe tab — separate component
 * from AgentFocusPanel itself (used by /openroom for the live-coding
 * animation view, a genuinely different use case) rather than overloading
 * one component with two unrelated visual registers.
 */
export function MemberDetailPanel({ agent, bureau, status, onClose }: MemberDetailPanelProps) {
  const [tab, setTab] = useState<SubTab>("apercu");
  const [loaded, setLoaded] = useState<Partial<Record<SubTab, boolean>>>({});

  function handleTabChange(next: string) {
    const nextTab = next as SubTab;
    setTab(nextTab);
    // Lazy-fetch: mark visited on first click, not on panel mount — avoids
    // firing 2 network calls (Performance + Mémoire) every time a card opens
    // if the user only ever looks at Aperçu.
    setLoaded((s) => (s[nextTab] ? s : { ...s, [nextTab]: true }));
  }

  return (
    <>
      <div className="fixed inset-0 z-40 bg-obsidian-deep/70" onClick={onClose} aria-hidden />
      <div className="fixed bottom-0 right-0 top-0 z-50 flex w-96 flex-col border-l border-copper/20 bg-obsidian shadow-[-8px_0_40px_rgba(0,0,0,0.6)]">
        <div className="flex items-center justify-between border-b border-copper/15 px-5 py-4">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{agent.icon}</span>
            <div>
              <h3 className="font-title font-medium text-ivoire">{agent.name}</h3>
              <p className="text-xs text-titane">{agent.role}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-titane transition-colors hover:text-ivoire"
            aria-label="Fermer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <Tabs
          value={tab}
          onValueChange={handleTabChange}
          className="flex min-h-0 flex-1 flex-col gap-0"
        >
          <TabsList className="mx-5 mt-3 w-fit">
            <TabsTrigger value="apercu">Aperçu</TabsTrigger>
            <TabsTrigger value="competences">Compétences</TabsTrigger>
            <TabsTrigger value="performance">Performance</TabsTrigger>
            <TabsTrigger value="memoire">Mémoire</TabsTrigger>
          </TabsList>

          <div className="min-h-0 flex-1 overflow-y-auto p-5">
            <TabsContent value="apercu" className="space-y-4">
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    "h-2 w-2 rounded-full",
                    status.status === "working" && "animate-pulse bg-copper",
                    status.status === "waiting" && "animate-pulse bg-titane/60",
                    status.status === "error" && "bg-red-500",
                    status.status === "idle" && "bg-titane/20"
                  )}
                />
                <span className="text-sm text-titane">{STATUS_LABEL[status.status]}</span>
              </div>

              {status.currentTask ? (
                <div className="rounded-lg border border-copper/10 bg-obsidian-2 p-3">
                  <p className="mb-1 text-[10px] uppercase tracking-widest text-titane/50">
                    Tâche
                  </p>
                  <p className="text-sm text-ivoire">{status.currentTask}</p>
                </div>
              ) : null}

              {status.status === "working" && typeof status.progress === "number" ? (
                <div>
                  <div className="mb-1 flex justify-between text-xs text-titane">
                    <span>Progression</span>
                    <span>{status.progress}%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-obsidian-3">
                    <div
                      className="h-full rounded-full bg-copper transition-all duration-500"
                      style={{ width: `${status.progress}%` }}
                    />
                  </div>
                </div>
              ) : null}

              {(status.log ?? []).length > 0 ? (
                <div>
                  <p className="mb-2 text-[10px] uppercase tracking-widest text-titane/50">
                    Log récent
                  </p>
                  <div className="max-h-48 space-y-1 overflow-y-auto rounded bg-obsidian-2 p-3 font-mono text-[10px] text-titane/60">
                    {(status.log ?? []).slice(-10).map((line, i) => (
                      <div key={i}>{line}</div>
                    ))}
                  </div>
                </div>
              ) : null}
            </TabsContent>

            <TabsContent value="competences" className="space-y-3">
              {agent.skills.length === 0 ? (
                <p className="text-sm text-titane/60">Aucune compétence renseignée.</p>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {agent.skills.map((skill) => (
                    <span
                      key={skill}
                      className="rounded-full border border-bronze-faint bg-obsidian-deep/50 px-2.5 py-1 text-xs text-titane/80"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="performance">
              {loaded.performance ? (
                <PerformanceTab agentId={agent.id} />
              ) : (
                <p className="text-sm text-titane/50">Chargement…</p>
              )}
            </TabsContent>

            <TabsContent value="memoire">
              {loaded.memoire ? <MemoireTab agent={agent} bureau={bureau} /> : (
                <p className="text-sm text-titane/50">Chargement…</p>
              )}
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </>
  );
}

export function PerformanceTab({ agentId }: { agentId: string }) {
  const [data, setData] = useState<{ days: number[]; calls: number; costUsd: number } | "loading" | "error">(
    "loading"
  );

  useEffect(() => {
    void fetchCostReport(30, agentId)
      .then((report) => {
        const days = Object.entries(report.by_day)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([, v]) => v);
        const agentTotals = report.by_agent[agentId];
        setData({
          days,
          calls: agentTotals?.calls ?? 0,
          costUsd: agentTotals?.cost_usd ?? 0,
        });
      })
      .catch(() => setData("error"));
  }, [agentId]);

  if (data === "loading") return <p className="text-sm text-titane/50">Chargement…</p>;
  if (data === "error")
    return <p className="text-sm text-titane/50">Historique indisponible pour le moment.</p>;
  if (data.calls === 0)
    return <p className="text-sm text-titane/50">Pas encore d&apos;historique pour cet agent.</p>;

  return (
    <div className="space-y-4">
      <div className="flex items-baseline gap-2">
        <span className="text-lg font-bold text-gradient-bronze">{data.calls}</span>
        <span className="text-xs text-titane/60">appels · 30 derniers jours</span>
      </div>
      <Sparkline data={data.days} width={280} height={56} className="w-full" />
      <p className="text-xs text-titane/50">Coût cumulé : ${data.costUsd.toFixed(2)}</p>
    </div>
  );
}

export function MemoireTab({ agent, bureau }: { agent: { id: string; role: string }; bureau: string }) {
  const [topics, setTopics] = useState<LibraryTopic[] | "loading" | "error">("loading");

  useEffect(() => {
    void fetchLibraryTopics({ bureau, limit: 20 })
      .then((res) => setTopics(res.topics))
      .catch(() => setTopics("error"));
  }, [bureau]);

  if (topics === "loading") return <p className="text-sm text-titane/50">Chargement…</p>;
  if (topics === "error" || topics.length === 0)
    return (
      <p className="text-sm text-titane/50">
        Aucun sujet appris pour le moment — {agent.role.toLowerCase()} construit sa mémoire au
        fil des tâches.
      </p>
    );

  return (
    <div className="flex flex-wrap gap-1.5">
      {topics.map((topic) => (
        <span
          key={topic.slug}
          className="rounded-full border border-bronze-faint bg-obsidian-deep/50 px-2.5 py-1 text-xs text-titane/80"
        >
          {topic.label}
        </span>
      ))}
    </div>
  );
}
