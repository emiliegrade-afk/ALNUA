"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ExternalLink } from "lucide-react";
import { AgentFeed } from "@/components/dashboard/agent-feed";
import { CeoPendingDossiersCard } from "@/components/ceo/ceo-pending-dossiers-card";
import { BureauPage } from "@/components/shared/bureau-page";
import { BureauPanel } from "@/components/shared/bureau-panel";
import { fetchTodayBriefing } from "@/lib/briefing-api";
import { fetchGithubPrs } from "@/lib/lobby-api";
import { fetchAgentLogs } from "@/lib/supabase";
import type { AgentLog } from "@/lib/types";

const AssistantChat = dynamic(
  () =>
    import("@/components/assistant/assistant-chat").then((m) => ({
      default: m.AssistantChat,
    })),
  {
    loading: () => (
      <div className="flex h-96 items-center justify-center rounded-2xl border border-bronze-faint bg-obsidian/70">
        <p className="text-sm text-titane/60">Chargement assistants…</p>
      </div>
    ),
  }
);

export default function CeoPage() {
  const [brief, setBrief] = useState<{
    summary?: string;
    urgent?: string[];
  } | null>(null);
  const [prs, setPrs] = useState<
    Array<{ number: number; title: string; html_url?: string; url?: string }>
  >([]);
  const [logs, setLogs] = useState<AgentLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [briefing, prData, logData] = await Promise.all([
        fetchTodayBriefing({ ensure: false, timeoutMs: 8_000 }).catch(
          () => null
        ),
        fetchGithubPrs(),
        fetchAgentLogs(5),
      ]);
      const urgent = (briefing?.raw_data?.tickets ?? [])
        .filter(
          (ticket) =>
            ticket.priority === "critical" || ticket.priority === "high"
        )
        .map(
          (ticket) =>
            `[${ticket.project_name ?? "?"}] ${ticket.title}`
        );
      setBrief(
        briefing
          ? {
              summary: briefing.summary,
              urgent: urgent.length > 0 ? urgent : undefined,
            }
          : null
      );
      setPrs(prData.slice(0, 5));
      setLogs(logData);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Impossible de charger le brief."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <BureauPage
      dept="ceo"
      title="Bureau du CEO"
      subtitle="Mission Control · Brief · Décisions en attente"
      breadcrumb="Bureau du CEO"
    >
      <div className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <AssistantChat variant="ceo" />
        </div>

        <div className="space-y-6 lg:col-span-2">
          <CeoPendingDossiersCard />

          <BureauPanel title="Brief du jour">
            <div className="mb-3 flex items-center justify-end">
              <Link
                href="/briefing"
                className="font-body text-xs text-bronze-bright hover:underline"
              >
                Historique →
              </Link>
            </div>
            {loading ? (
              <p className="font-body text-sm text-titane/60">Chargement…</p>
            ) : error ? (
              <p className="font-body text-sm text-red-400">{error}</p>
            ) : brief?.summary ? (
              <p className="whitespace-pre-line font-body text-sm leading-relaxed text-ivoire/90">
                {brief.summary}
              </p>
            ) : (
              <p className="font-body text-sm text-titane/60">Brief indisponible.</p>
            )}
            {brief?.urgent && brief.urgent.length > 0 ? (
              <ul className="mt-3 space-y-1 border-t border-bronze-faint pt-3">
                {brief.urgent.map((item) => (
                  <li key={item} className="font-body text-xs text-bronze-bright">
                    {item}
                  </li>
                ))}
              </ul>
            ) : null}
          </BureauPanel>

          <AgentFeed logs={logs} loading={loading} />

          <BureauPanel title="PRs GitHub">
            <p className="label-caps mb-4">
              Pull requests ouvertes (hors dossiers R&D)
            </p>
            {prs.length === 0 ? (
              <p className="font-body text-sm text-titane/60">Aucune PR en attente.</p>
            ) : (
              <ul className="space-y-2">
                {prs.map((pr) => (
                  <li key={pr.number}>
                    <a
                      href={pr.html_url ?? pr.url ?? "#"}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-start gap-2 font-body text-sm text-ivoire/80 transition hover:text-ivoire"
                    >
                      <ExternalLink className="mt-0.5 h-3.5 w-3.5 shrink-0 text-bronze" />
                      <span>
                        #{pr.number} — {pr.title}
                      </span>
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </BureauPanel>
        </div>
      </div>
    </BureauPage>
  );
}
