"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ExternalLink } from "lucide-react";
import { AgentFeed } from "@/components/dashboard/agent-feed";
import { COOChat } from "@/components/dashboard/coo-chat";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { DepartmentHeader } from "@/components/shared/department-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchTodayBriefing } from "@/lib/briefing-api";
import { fetchGithubPrs } from "@/lib/lobby-api";
import { fetchAgentLogs } from "@/lib/supabase";
import type { AgentLog } from "@/lib/types";

export default function CeoPage() {
  const [brief, setBrief] = useState<{
    summary?: string;
    urgent?: string[];
  } | null>(null);
  const [prs, setPrs] = useState<
    Array<{ number: number; title: string; html_url?: string; url?: string }>
  >([]);
  const [logs, setLogs] = useState<AgentLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [briefing, prData, logData] = await Promise.all([
        fetchTodayBriefing(),
        fetchGithubPrs(),
        fetchAgentLogs(5),
      ]);
      const urgent = briefing.raw_data.tickets
        .filter(
          (ticket) =>
            ticket.priority === "critical" || ticket.priority === "high"
        )
        .map(
          (ticket) =>
            `[${ticket.project_name ?? "?"}] ${ticket.title}`
        );
      setBrief({
        summary: briefing.summary,
        urgent: urgent.length > 0 ? urgent : undefined,
      });
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
    <>
      <BackToLobby />
      <DepartmentHeader
        dept="ceo"
        title="Bureau du CEO"
        subtitle="Mission Control · Brief · Décisions en attente"
        breadcrumb="Bureau du CEO"
      />

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <COOChat variant="ceo" />
        </div>

        <div className="space-y-6 lg:col-span-2">
          <Card className="border-copper/20 bg-obsidian-2/90">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between gap-2">
                <CardTitle className="font-title text-base text-ivory">
                  Brief du jour
                </CardTitle>
                <Link
                  href="/briefing"
                  className="font-body text-xs text-copper hover:underline"
                >
                  Historique →
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <p className="font-body text-sm text-titanium/60">Chargement…</p>
              ) : error ? (
                <p className="font-body text-sm text-red-400">{error}</p>
              ) : brief?.summary ? (
                <p className="whitespace-pre-line font-body text-sm leading-relaxed text-ivory/90">
                  {brief.summary}
                </p>
              ) : (
                <p className="font-body text-sm text-titanium/60">
                  Brief indisponible.
                </p>
              )}
              {brief?.urgent && brief.urgent.length > 0 ? (
                <ul className="mt-3 space-y-1 border-t border-copper/10 pt-3">
                  {brief.urgent.map((item) => (
                    <li key={item} className="font-body text-xs text-copper">
                      {item}
                    </li>
                  ))}
                </ul>
              ) : null}
            </CardContent>
          </Card>

          <AgentFeed logs={logs} loading={loading} />

          <Card className="border-copper/20 bg-obsidian-2/90">
            <CardHeader className="pb-2">
              <CardTitle className="font-title text-base text-ivory">
                Décisions en attente
              </CardTitle>
              <p className="font-body text-xs text-titanium/60">
                PRs GitHub ouvertes
              </p>
            </CardHeader>
            <CardContent>
              {prs.length === 0 ? (
                <p className="font-body text-sm text-titanium/60">
                  Aucune PR en attente.
                </p>
              ) : (
                <ul className="space-y-2">
                  {prs.map((pr) => (
                    <li key={pr.number}>
                      <a
                        href={pr.html_url ?? pr.url ?? "#"}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-start gap-2 font-body text-sm text-ivory/80 transition hover:text-ivory"
                      >
                        <ExternalLink className="mt-0.5 h-3.5 w-3.5 shrink-0 text-copper" />
                        <span>
                          #{pr.number} — {pr.title}
                        </span>
                      </a>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
}
