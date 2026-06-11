"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import Link from "next/link";
import {
  Copy,
  Download,
  FlaskConical,
  Loader2,
  Search,
} from "lucide-react";
import { toast } from "sonner";
import { BetaFeedbackDetailPanel } from "@/components/beta/beta-feedback-detail-panel";
import { BetaStatsCharts } from "@/components/beta/beta-stats-charts";
import { BetaTypeDonut } from "@/components/beta/beta-type-donut";
import {
  BETA_FEEDBACK_TYPES,
  BETA_SEVERITIES,
  BETA_TYPE_LABELS,
  severityStyle,
} from "@/components/beta/beta.constants";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { fetchProjects } from "@/lib/api";
import {
  betaTestersCsvUrl,
  createBetaInvite,
  fetchBetaFeedbackList,
  fetchBetaStats,
  fetchBetaTesters,
  type BetaFeedback,
  type BetaStats,
  type BetaTester,
} from "@/lib/beta-api";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";

type BetaTab = "feedbacks" | "testers" | "stats";

export function BetaView() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectFilter, setProjectFilter] = useState("all");
  const [tab, setTab] = useState<BetaTab>("feedbacks");
  const [loading, setLoading] = useState(true);

  const [stats, setStats] = useState<BetaStats | null>(null);
  const [testers, setTesters] = useState<BetaTester[]>([]);
  const [feedbacks, setFeedbacks] = useState<BetaFeedback[]>([]);

  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [search, setSearch] = useState("");

  const [selectedFeedback, setSelectedFeedback] = useState<BetaFeedback | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [inviteLoading, setInviteLoading] = useState(false);

  const projectId = projectFilter === "all" ? undefined : projectFilter;

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [s, t, f] = await Promise.all([
        fetchBetaStats(projectId),
        fetchBetaTesters(projectId),
        fetchBetaFeedbackList({ project_id: projectId }),
      ]);
      setStats(s);
      setTesters(t);
      setFeedbacks(f);
    } catch {
      setStats(null);
      setTesters([]);
      setFeedbacks([]);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchProjects().then(setProjects).catch(() => setProjects([]));
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const filteredFeedbacks = useMemo(() => {
    return feedbacks.filter((f) => {
      if (typeFilter !== "all" && f.type !== typeFilter) return false;
      if (severityFilter !== "all" && f.severity !== severityFilter) return false;
      return true;
    });
  }, [feedbacks, typeFilter, severityFilter]);

  const filteredTesters = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return testers;
    return testers.filter(
      (t) =>
        t.email.toLowerCase().includes(q) ||
        (t.first_name ?? "").toLowerCase().includes(q)
    );
  }, [testers, search]);

  const handleCopyInvite = async () => {
    if (projectFilter === "all") {
      toast.error("Sélectionne un projet pour copier le lien");
      return;
    }
    setInviteLoading(true);
    try {
      const { invite_url } = await createBetaInvite(projectFilter);
      await navigator.clipboard.writeText(invite_url);
      toast.success("Lien d'invitation copié !");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    } finally {
      setInviteLoading(false);
    }
  };

  const tabs: { id: BetaTab; label: string }[] = [
    { id: "feedbacks", label: "Feedbacks" },
    { id: "testers", label: "Testeurs" },
    { id: "stats", label: "Stats" },
  ];

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-copper/30 bg-copper/10">
            <FlaskConical className="h-5 w-5 text-copper" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-ivory">Beta Testeurs</h1>
            <p className="text-sm text-titanium">
              Portail feedback — Naïa, Eve et futurs programmes
            </p>
          </div>
        </div>

        <Select value={projectFilter} onValueChange={setProjectFilter}>
          <SelectTrigger className="w-[200px] border-white/10 bg-surface">
            <SelectValue placeholder="Projet" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tous les projets</SelectItem>
            {projects.map((p) => (
              <SelectItem key={p.id} value={p.id}>
                {p.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </header>

      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <aside className="space-y-4">
          <Card className="border-white/10 bg-surface/80">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-ivory">Stats</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {loading ? (
                <Loader2 className="h-5 w-5 animate-spin text-copper/50" />
              ) : (
                <>
                  <div>
                    <p className="text-2xl font-semibold text-ivory">
                      {stats?.total_testers ?? 0}
                    </p>
                    <p className="text-xs text-titanium">Testeurs actifs</p>
                  </div>
                  <div>
                    <p className="text-2xl font-semibold text-copper-glow">
                      {stats?.feedback_this_week ?? 0}
                    </p>
                    <p className="text-xs text-titanium">Feedbacks cette semaine</p>
                  </div>
                  <div>
                    <p className="text-2xl font-semibold text-ivory/80">
                      {stats?.total_feedback ?? 0}
                    </p>
                    <p className="text-xs text-titanium">Total feedbacks</p>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {stats ? <BetaTypeDonut byType={stats.by_type} compact /> : null}

          <div className="space-y-2">
            <Button
              variant="outline"
              className="w-full justify-start gap-2 border-copper/25 text-copper-glow"
              onClick={handleCopyInvite}
              disabled={inviteLoading || projectFilter === "all"}
            >
              {inviteLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
              Copier le lien d&apos;invitation
            </Button>
            <Button
              variant="outline"
              className="w-full justify-start gap-2 border-white/10"
              asChild
            >
              <a href={betaTestersCsvUrl(projectId)} download>
                <Download className="h-4 w-4" />
                Télécharger CSV testeurs
              </a>
            </Button>
          </div>
        </aside>

        <section className="min-w-0 space-y-4">
          <div className="flex gap-1 rounded-lg border border-white/10 bg-surface/50 p-1">
            {tabs.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setTab(t.id)}
                className={cn(
                  "flex-1 rounded-md px-3 py-2 text-sm font-medium transition",
                  tab === t.id
                    ? "bg-copper/15 text-copper-glow"
                    : "text-titanium hover:text-ivory"
                )}
              >
                {t.label}
              </button>
            ))}
          </div>

          {tab === "feedbacks" ? (
            <div className="space-y-4">
              <div className="flex flex-wrap gap-2">
                <Select value={typeFilter} onValueChange={setTypeFilter}>
                  <SelectTrigger className="w-[160px] border-white/10 bg-surface">
                    <SelectValue placeholder="Type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Tous types</SelectItem>
                    {BETA_FEEDBACK_TYPES.map((t) => (
                      <SelectItem key={t.id} value={t.id}>
                        {t.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={severityFilter} onValueChange={setSeverityFilter}>
                  <SelectTrigger className="w-[160px] border-white/10 bg-surface">
                    <SelectValue placeholder="Sévérité" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Toutes sévérités</SelectItem>
                    {BETA_SEVERITIES.map((s) => (
                      <SelectItem key={s.id} value={s.id}>
                        {s.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {loading ? (
                <div className="flex justify-center py-12">
                  <Loader2 className="h-6 w-6 animate-spin text-copper/50" />
                </div>
              ) : filteredFeedbacks.length === 0 ? (
                <p className="py-12 text-center text-sm text-titanium">
                  Aucun feedback pour ces filtres
                </p>
              ) : (
                <ul className="space-y-2">
                  {filteredFeedbacks.map((f) => (
                    <li key={f.id}>
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedFeedback(f);
                          setDetailOpen(true);
                        }}
                        className="w-full rounded-xl border border-white/10 bg-surface/60 p-4 text-left transition hover:border-copper/25 hover:bg-surface"
                      >
                        <div className="flex flex-wrap items-start justify-between gap-2">
                          <div className="min-w-0">
                            <p className="font-medium text-ivory">{f.title}</p>
                            <p className="mt-1 text-xs text-titanium">
                              {f.tester_name ?? f.tester_email} · {f.project_name} ·{" "}
                              {format(new Date(f.created_at), "d MMM yyyy", {
                                locale: fr,
                              })}
                            </p>
                          </div>
                          <div className="flex shrink-0 flex-wrap gap-2">
                            <Badge
                              variant="outline"
                              className={severityStyle(f.severity)}
                            >
                              {f.severity ?? "—"}
                            </Badge>
                            <Badge variant="outline" className="border-white/10 text-titanium">
                              {BETA_TYPE_LABELS[f.type ?? "autre"]}
                            </Badge>
                          </div>
                        </div>
                        {f.ticket_id ? (
                          <Link
                            href={`/tickets?id=${f.ticket_id}`}
                            onClick={(e) => e.stopPropagation()}
                            className="mt-2 inline-flex text-xs text-copper-glow hover:underline"
                          >
                            🎟️ Ticket créé
                          </Link>
                        ) : null}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ) : null}

          {tab === "testers" ? (
            <div className="space-y-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-titanium/50" />
                <Input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Rechercher par email ou prénom…"
                  className="border-white/10 bg-surface pl-9"
                />
              </div>

              {loading ? (
                <div className="flex justify-center py-12">
                  <Loader2 className="h-6 w-6 animate-spin text-copper/50" />
                </div>
              ) : (
                <div className="overflow-x-auto rounded-xl border border-white/10">
                  <table className="w-full min-w-[600px] text-sm">
                    <thead>
                      <tr className="border-b border-white/10 bg-white/[0.02] text-left text-xs text-titanium">
                        <th className="px-4 py-3 font-medium">Prénom</th>
                        <th className="px-4 py-3 font-medium">Email</th>
                        <th className="px-4 py-3 font-medium">Appareil</th>
                        <th className="px-4 py-3 font-medium text-center">Feedbacks</th>
                        <th className="px-4 py-3 font-medium">Inscription</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredTesters.map((t) => (
                        <tr
                          key={t.id}
                          className="border-b border-white/5 text-ivory/90 last:border-0"
                        >
                          <td className="px-4 py-3">{t.first_name ?? "—"}</td>
                          <td className="px-4 py-3 text-titanium">{t.email}</td>
                          <td className="px-4 py-3 text-titanium">
                            {t.device ?? "—"}
                            {t.os_version ? ` · ${t.os_version}` : ""}
                          </td>
                          <td className="px-4 py-3 text-center font-medium text-copper-glow">
                            {t.feedback_count}
                          </td>
                          <td className="px-4 py-3 text-titanium">
                            {format(new Date(t.joined_at), "d MMM yyyy", { locale: fr })}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {filteredTesters.length === 0 ? (
                    <p className="py-8 text-center text-sm text-titanium">
                      Aucune testeuse trouvée
                    </p>
                  ) : null}
                </div>
              )}
            </div>
          ) : null}

          {tab === "stats" && stats ? <BetaStatsCharts stats={stats} /> : null}
          {tab === "stats" && !stats && !loading ? (
            <p className="py-12 text-center text-sm text-titanium">Pas de données</p>
          ) : null}
        </section>
      </div>

      <BetaFeedbackDetailPanel
        feedback={selectedFeedback}
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
      />
    </div>
  );
}
