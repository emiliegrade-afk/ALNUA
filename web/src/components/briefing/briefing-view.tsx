"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { format, parseISO } from "date-fns";
import { fr } from "date-fns/locale";
import {
  Calendar,
  ChevronDown,
  ChevronUp,
  Clock,
  Flame,
  Loader2,
  Newspaper,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { toast } from "sonner";
import { BriefingCooPanel } from "@/components/briefing/briefing-coo-panel";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { ROUTES } from "@/lib/routes";
import { MarkdownContent } from "@/components/shared/markdown-content";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  fetchAdminFlags,
  isBriefingCooSectionEnabled,
  type AdminFlags,
} from "@/lib/admin-flags-api";
import {
  fetchBriefingHistory,
  fetchCooDailyBriefing,
  fetchTodayBriefing,
  generateBriefingNow,
  type CooDailyBriefing,
  type DailyBriefing,
} from "@/lib/briefing-api";
import { cn } from "@/lib/utils";

type BriefingTab = "operational" | "coo";

const COO_CACHE_KEY = "alnua-coo-brief-cache";

function readCooCache(): CooDailyBriefing | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(COO_CACHE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as CooDailyBriefing;
    return parsed?.date ? parsed : null;
  } catch {
    return null;
  }
}

function writeCooCache(brief: CooDailyBriefing) {
  try {
    sessionStorage.setItem(COO_CACHE_KEY, JSON.stringify(brief));
  } catch {
    /* ignore quota */
  }
}

function formatBriefingDate(dateStr: string): string {
  try {
    return format(parseISO(dateStr), "EEEE d MMMM yyyy", { locale: fr });
  } catch {
    return dateStr;
  }
}

function formatShortDate(dateStr: string): string {
  try {
    return format(parseISO(dateStr), "d MMM yyyy", { locale: fr });
  } catch {
    return dateStr;
  }
}

function RawDataAccordion({ briefing }: { briefing: DailyBriefing }) {
  const [open, setOpen] = useState(false);
  const raw = briefing.raw_data ?? {};
  const tickets = raw.tickets ?? [];
  const posts = raw.posts ?? [];
  const roadmap = raw.roadmap ?? [];

  return (
    <div className="rounded-xl border border-copper/15 bg-obsidian-deep/40">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-4 py-3 text-left text-sm text-titanium hover:text-ivory"
      >
        <span>Données brutes</span>
        {open ? (
          <ChevronUp className="h-4 w-4" />
        ) : (
          <ChevronDown className="h-4 w-4" />
        )}
      </button>
      {open && (
        <div className="space-y-4 border-t border-copper/15 px-4 py-4 text-sm">
          <section>
            <div className="mb-2 flex items-center justify-between">
              <h4 className="font-medium text-ivory">Tickets urgents</h4>
              <Link
                href={ROUTES.tickets}
                className="text-xs text-copper hover:text-copper-glow"
              >
                Voir tous →
              </Link>
            </div>
            {tickets.length === 0 ? (
              <p className="text-xs text-titanium">Aucun ticket urgent.</p>
            ) : (
              <ul className="space-y-1.5">
                {tickets.slice(0, 5).map((t) => (
                  <li
                    key={t.id}
                    className="rounded-lg border border-copper/10 bg-obsidian-deep/40 px-3 py-2 text-xs text-ivory/80"
                  >
                    <span className="text-copper-glow">{t.priority}</span>
                    {" · "}
                    {t.title}
                    {t.project_name ? (
                      <span className="text-titanium"> — {t.project_name}</span>
                    ) : null}
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section>
            <div className="mb-2 flex items-center justify-between">
              <h4 className="font-medium text-ivory">Posts en attente</h4>
              <Link
                href={ROUTES.content}
                className="text-xs text-copper hover:text-copper-glow"
              >
                Voir tous →
              </Link>
            </div>
            {posts.length === 0 ? (
              <p className="text-xs text-titanium">Aucun post en attente.</p>
            ) : (
              <ul className="space-y-1.5">
                {posts.slice(0, 5).map((p) => (
                  <li
                    key={p.id}
                    className="rounded-lg border border-copper/10 bg-obsidian-deep/40 px-3 py-2 text-xs text-ivory/80"
                  >
                    <span className="text-copper-glow">{p.platform}</span>
                    {" · "}
                    {p.text_content.slice(0, 80)}
                    {p.text_content.length > 80 ? "…" : ""}
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section>
            <div className="mb-2 flex items-center justify-between">
              <h4 className="font-medium text-ivory">Roadmap imminente</h4>
              <Link
                href={ROUTES.roadmap}
                className="text-xs text-copper hover:text-copper-glow"
              >
                Voir roadmap →
              </Link>
            </div>
            {roadmap.length === 0 ? (
              <p className="text-xs text-titanium">
                Aucune échéance dans les 7 prochains jours.
              </p>
            ) : (
              <ul className="space-y-1.5">
                {roadmap.slice(0, 5).map((r) => (
                  <li
                    key={r.id}
                    className="rounded-lg border border-copper/10 bg-obsidian-deep/40 px-3 py-2 text-xs text-ivory/80"
                  >
                    {r.title}
                    {r.due_date ? (
                      <span className="text-titanium">
                        {" "}
                        — {formatShortDate(r.due_date)}
                      </span>
                    ) : null}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}
    </div>
  );
}

function CounterPill({
  icon,
  label,
  value,
  accent,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  accent: string;
}) {
  return (
    <div className="flex flex-1 flex-col items-center gap-1 rounded-xl border border-copper/15 bg-obsidian-deep/50 px-4 py-3">
      <div className={cn("flex items-center gap-1.5 text-lg font-semibold", accent)}>
        {icon}
        {value}
      </div>
      <span className="text-center text-[11px] text-titanium">{label}</span>
    </div>
  );
}

function extractCooFromGenerateResult(
  result: DailyBriefing
): CooDailyBriefing | null {
  const orch = result.orchestration as
    | { briefing_result?: CooDailyBriefing }
    | undefined;
  const brief = orch?.briefing_result;
  return brief?.coo_brief ? brief : null;
}

export function BriefingView() {
  const [history, setHistory] = useState<DailyBriefing[]>([]);
  const [selected, setSelected] = useState<DailyBriefing | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<BriefingTab>("operational");
  const [adminFlags, setAdminFlags] = useState<AdminFlags | null>(null);
  const [preview, setPreview] = useState(false);
  const [cooBriefing, setCooBriefing] = useState<CooDailyBriefing | null>(null);
  const [cooLoading, setCooLoading] = useState(false);

  const cooTabEnabled = isBriefingCooSectionEnabled(adminFlags, preview);
  const unifiedGenerate = adminFlags?.briefing_unified_generate ?? false;

  useEffect(() => {
    if (typeof window !== "undefined") {
      setPreview(new URLSearchParams(window.location.search).get("preview") === "1");
    }
    fetchAdminFlags().then(setAdminFlags).catch(() => setAdminFlags(null));
    setCooBriefing(readCooCache());
  }, []);

  const loadOperational = useCallback(async (preferId?: string) => {
    setLoading(true);
    setError(null);
    try {
      const [todayResult, past] = await Promise.all([
        fetchTodayBriefing({ ensure: false }).catch(() => null),
        fetchBriefingHistory(30),
      ]);
      const merged = todayResult
        ? [todayResult, ...past.filter((b) => b.id !== todayResult.id)]
        : past;
      setHistory(merged);
      if (preferId) {
        const found = merged.find((b) => b.id === preferId);
        setSelected(found ?? todayResult ?? merged[0] ?? null);
      } else {
        setSelected(todayResult ?? merged[0] ?? null);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Impossible de charger le briefing."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadOperational();
  }, [loadOperational]);

  const loadCooBriefing = useCallback(async () => {
    setCooLoading(true);
    try {
      const brief = await fetchCooDailyBriefing();
      setCooBriefing(brief);
      writeCooCache(brief);
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Échec du brief COO"
      );
    } finally {
      setCooLoading(false);
    }
  }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const fresh = await generateBriefingNow();
      const cooFromOrch = extractCooFromGenerateResult(fresh);
      if (cooFromOrch) {
        setCooBriefing(cooFromOrch);
        writeCooCache(cooFromOrch);
      }
      toast.success(
        fresh.unified
          ? "Briefing opérationnel + orchestration COO envoyés"
          : "Briefing opérationnel généré"
      );
      await loadOperational(fresh.id);
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Échec de la génération"
      );
    } finally {
      setGenerating(false);
    }
  };

  const isEmpty = !loading && history.length === 0 && activeTab === "operational";
  const roadmapCount = selected?.raw_data?.roadmap?.length ?? 0;

  return (
    <div className="space-y-6">
      <BackToLobby />
      <header className="flex flex-wrap items-start justify-between gap-4 pt-10">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-copper/15">
            <Newspaper className="h-5 w-5 text-copper" />
          </div>
          <div>
            <h1 className="text-2xl font-medium tracking-tight text-ivory">
              Briefing matinal
            </h1>
            <p className="text-sm text-titanium">
              Opérationnel (tickets, posts) · Exécutif COO (trends, coûts)
            </p>
          </div>
        </div>
        <Button
          onClick={() => void handleGenerate()}
          disabled={generating || loading}
          className="bg-copper/20 text-copper-glow hover:bg-copper/30"
        >
          {generating ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="mr-2 h-4 w-4" />
          )}
          {generating
            ? "Génération…"
            : unifiedGenerate
              ? "Regénérer (op + COO)"
              : "Regénérer"}
        </Button>
      </header>

      {cooTabEnabled && (
        <div className="flex gap-1 rounded-lg border border-copper/15 bg-obsidian-deep/40 p-1">
          <button
            type="button"
            onClick={() => setActiveTab("operational")}
            className={cn(
              "flex flex-1 items-center justify-center gap-2 rounded-md px-4 py-2 text-sm transition",
              activeTab === "operational"
                ? "bg-copper/15 text-ivory"
                : "text-titanium hover:text-ivory"
            )}
          >
            <Newspaper className="h-4 w-4" />
            Opérationnel
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("coo")}
            className={cn(
              "flex flex-1 items-center justify-center gap-2 rounded-md px-4 py-2 text-sm transition",
              activeTab === "coo"
                ? "bg-copper/15 text-ivory"
                : "text-titanium hover:text-ivory"
            )}
          >
            <Sparkles className="h-4 w-4" />
            Brief COO
          </button>
        </div>
      )}

      {activeTab === "coo" && cooTabEnabled ? (
        <BriefingCooPanel
          briefing={cooBriefing}
          loading={cooLoading}
          onRefresh={() => void loadCooBriefing()}
        />
      ) : loading ? (
        <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
          <Skeleton className="h-96 rounded-xl bg-obsidian/50" />
          <Skeleton className="h-96 rounded-xl bg-obsidian/50" />
        </div>
      ) : isEmpty ? (
        <Card className="border-copper/20 bg-surface/60">
          <CardContent className="flex flex-col items-center gap-4 py-16 text-center">
            <Clock className="h-10 w-10 text-copper/60" />
            <p className="max-w-md text-sm leading-relaxed text-titanium">
              Ton premier briefing sera prêt demain matin à 8h. Clique sur
              &quot;Générer maintenant&quot; pour en créer un tout de suite.
            </p>
            <Button
              onClick={() => void handleGenerate()}
              disabled={generating}
              className="bg-copper text-obsidian hover:bg-copper-glow"
            >
              {generating ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              Générer maintenant
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
          <aside className="space-y-2">
            <p className="px-1 text-xs font-medium uppercase tracking-wider text-titanium">
              Historique
            </p>
            <nav className="space-y-1">
              {history.map((item) => {
                const active = selected?.id === item.id;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setSelected(item)}
                    className={cn(
                      "flex w-full items-center gap-2 rounded-lg border px-3 py-2.5 text-left text-sm transition",
                      active
                        ? "border-copper/40 bg-copper/10 text-ivory"
                        : "border-transparent text-titanium hover:border-copper/20 hover:bg-obsidian-deep/50"
                    )}
                  >
                    <Calendar className="h-3.5 w-3.5 shrink-0 opacity-60" />
                    <span className="flex-1 truncate">
                      {formatShortDate(item.date)}
                    </span>
                    {item.has_urgent ? (
                      <span className="rounded-full bg-red-500/20 px-1.5 text-[10px] font-medium text-red-400">
                        {item.urgent_count}
                      </span>
                    ) : item.pending_count > 0 ? (
                      <span className="rounded-full bg-amber-500/20 px-1.5 text-[10px] font-medium text-amber-400">
                        {item.pending_count}
                      </span>
                    ) : null}
                  </button>
                );
              })}
            </nav>
          </aside>

          <div className="space-y-4">
            {error ? (
              <p className="text-sm text-red-400">{error}</p>
            ) : null}

            {selected ? (
              <>
                <Card className="border-copper/20 bg-surface/80">
                  <CardHeader>
                    <CardTitle className="text-xl capitalize text-ivory">
                      {formatBriefingDate(selected.date)}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="flex flex-wrap gap-3">
                      <CounterPill
                        icon={<Flame className="h-4 w-4" />}
                        label="Urgent"
                        value={selected.urgent_count}
                        accent="text-red-400"
                      />
                      <CounterPill
                        icon={<span>⏳</span>}
                        label="En attente"
                        value={selected.pending_count}
                        accent="text-amber-400"
                      />
                      <CounterPill
                        icon={<span>📅</span>}
                        label="Roadmap"
                        value={roadmapCount}
                        accent="text-copper-glow"
                      />
                    </div>

                    <MarkdownContent className="prose prose-invert prose-sm max-w-none prose-headings:text-ivory prose-p:text-ivory/85 prose-li:text-ivory/85">
                      {selected.summary}
                    </MarkdownContent>
                  </CardContent>
                </Card>

                <RawDataAccordion briefing={selected} />
              </>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
