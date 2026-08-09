"use client";

import { useEffect, useMemo, useState } from "react";
import { computePostStats, fetchPosts, type Post } from "@/lib/content";
import { PLATFORMS, SECTORS } from "@/components/content/content.constants";
import { fetchLeaderboard } from "@/lib/marketing-api";
import { currentMonthKey, fetchFinanceTransactions, formatCurrency } from "@/lib/finances-api";
import { getAgentsForBureau } from "@/lib/agent-bureau";
import { fetchProjects } from "@/lib/api";
import type { Project } from "@/lib/types";
import { CampaignsPreviewPanel } from "@/components/marketing/campaigns-preview-panel";
import { TodayContentPanel } from "@/components/marketing/today-content-panel";
import { PerformanceByPlatformPanel } from "@/components/marketing/performance-by-platform-panel";
import { TopContentPanel } from "@/components/marketing/top-content-panel";
import { ConversionFunnelPanel } from "@/components/marketing/conversion-funnel-panel";
import { C } from "../app-v2/shared";
import { PremiumPanel, PremiumKpiTile } from "./premium";

/* Onglet "Vue globale" — Marketing Command Center. Échelle premium (Phase
   38, ROADMAP.md) : chiffres 27px mono, cartes spacieuses — cf.
   premium.tsx. Toujours uniquement des données réelles : posts_queue,
   leaderboard de compétition, dépenses catégorie "marketing", campagnes
   réelles (Phase 33), calendrier réel, performances/entonnoir/top contenus
   (Phase 37, saisie manuelle). Pas d'historique temporel marketing réel
   (vérifié) → les sparklines des 5 tuiles historiques sont des lignes
   plates honnêtes (flatTrend), pas une série inventée — même précédent que
   web/src/lib/console/rich-data.ts. */

/** Ligne plate honnête — aucun historique marketing réel disponible. */
function flatTrend(v: number): number[] {
  return Array.from({ length: 6 }, () => Math.max(0, v));
}

export function VueGlobaleTab({ onOpenCampagnes }: { onOpenCampagnes?: () => void }) {
  const [posts, setPosts] = useState<Post[]>([]);
  const [postsLoading, setPostsLoading] = useState(true);
  const [teamScore, setTeamScore] = useState<number | null>(null);
  const [marketingSpend, setMarketingSpend] = useState<number | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);

  useEffect(() => {
    let cancelled = false;
    setPostsLoading(true);
    fetchPosts()
      .then((p) => {
        if (!cancelled) setPosts(p);
      })
      .catch(() => {
        if (!cancelled) setPosts([]);
      })
      .finally(() => {
        if (!cancelled) setPostsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetchProjects()
      .then((p) => {
        if (!cancelled) setProjects(p);
      })
      .catch(() => {
        if (!cancelled) setProjects([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    const marketingAgentIds = new Set(getAgentsForBureau("marketing").map((a) => a.id));
    fetchLeaderboard()
      .then((entries) => {
        if (cancelled) return;
        const total = entries
          .filter((e) => marketingAgentIds.has(e.agent_id))
          .reduce((sum, e) => sum + e.score, 0);
        setTeamScore(total);
      })
      .catch(() => {
        if (!cancelled) setTeamScore(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetchFinanceTransactions({ month: currentMonthKey(), category: "marketing" })
      .then((txs) => {
        if (!cancelled) setMarketingSpend(txs.filter((t) => t.type === "expense").reduce((sum, t) => sum + t.amount, 0));
      })
      .catch(() => {
        if (!cancelled) setMarketingSpend(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const stats = useMemo(() => computePostStats(posts), [posts]);

  const byPlatform = useMemo(() => {
    const total = posts.length || 1;
    return PLATFORMS.map((p) => ({
      ...p,
      count: posts.filter((post) => post.platform === p.id).length,
      pct: Math.round((posts.filter((post) => post.platform === p.id).length / total) * 100),
    })).filter((p) => p.count > 0);
  }, [posts]);

  const bySector = useMemo(() => {
    const total = posts.length || 1;
    return SECTORS.map((s) => ({
      ...s,
      count: posts.filter((post) => post.sector === s.id).length,
      pct: Math.round((posts.filter((post) => post.sector === s.id).length / total) * 100),
    })).filter((s) => s.count > 0);
  }, [posts]);

  return (
    <div className="alnua-scroll flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-1">
      {postsLoading && posts.length === 0 ? (
        <p className="text-center text-[11px]" style={{ color: C.faint }}>
          Chargement de la file de publication…
        </p>
      ) : (
        <div className="flex flex-wrap gap-3">
          <PremiumKpiTile label="EN ATTENTE" value={stats.pending} caption="file actuelle" trend={flatTrend(stats.pending)} />
          <PremiumKpiTile
            label="APPROUVÉS · 7J"
            value={stats.approvedThisWeek}
            caption="7 derniers jours"
            trend={flatTrend(stats.approvedThisWeek)}
            trendColor="#7FC98C"
          />
          <PremiumKpiTile
            label="PUBLIÉS CE MOIS"
            value={stats.publishedThisMonth}
            caption="mois en cours"
            trend={flatTrend(stats.publishedThisMonth)}
            trendColor="#7FC98C"
          />
          <PremiumKpiTile
            label="SCORE ÉQUIPE"
            value={teamScore ?? "—"}
            caption="compétition, mois en cours"
            trend={teamScore != null ? flatTrend(teamScore) : undefined}
          />
          <PremiumKpiTile
            label="DÉPENSES · MOIS"
            value={marketingSpend != null ? formatCurrency(marketingSpend) : "—"}
            caption="catégorie marketing"
            trend={marketingSpend != null ? flatTrend(marketingSpend) : undefined}
            trendColor="#f87171"
          />
        </div>
      )}

      <CampaignsPreviewPanel onSeeAll={onOpenCampagnes} />

      <div className="grid gap-3 lg:grid-cols-2">
        <PerformanceByPlatformPanel />
        <ConversionFunnelPanel projects={projects} />
        <TopContentPanel posts={posts} />
        <TodayContentPanel />

        <PremiumPanel title="Répartition par plateforme">
          {byPlatform.length === 0 ? (
            <p className="text-[11px]" style={{ color: C.faint }}>
              Aucun post pour l&apos;instant.
            </p>
          ) : (
            <div className="flex flex-col gap-2.5">
              {byPlatform.map((p) => (
                <div key={p.id} className="flex items-center gap-3">
                  <span className="w-[92px] shrink-0 truncate text-[11px]" style={{ color: C.warm }}>
                    {p.label}
                  </span>
                  <span className="h-1.5 flex-1 overflow-hidden rounded-full" style={{ background: "rgba(192,138,114,.14)" }}>
                    <span className="block h-full rounded-full" style={{ width: `${p.pct}%`, background: `linear-gradient(90deg,#8A6050,${C.copperLight})` }} />
                  </span>
                  <span className="w-8 shrink-0 text-right text-[11px]" style={{ color: C.ivory }}>
                    {p.count}
                  </span>
                </div>
              ))}
            </div>
          )}
        </PremiumPanel>

        <PremiumPanel title="Répartition par secteur">
          {bySector.length === 0 ? (
            <p className="text-[11px]" style={{ color: C.faint }}>
              Aucun post pour l&apos;instant.
            </p>
          ) : (
            <div className="flex flex-col gap-2.5">
              {bySector.map((s) => (
                <div key={s.id} className="flex items-center gap-3">
                  <span className="w-[92px] shrink-0 truncate text-[11px]" style={{ color: C.warm }}>
                    {s.label}
                  </span>
                  <span className="h-1.5 flex-1 overflow-hidden rounded-full" style={{ background: "rgba(192,138,114,.14)" }}>
                    <span className="block h-full rounded-full" style={{ width: `${s.pct}%`, background: `linear-gradient(90deg,#8A6050,${C.copperLight})` }} />
                  </span>
                  <span className="w-8 shrink-0 text-right text-[11px]" style={{ color: C.ivory }}>
                    {s.count}
                  </span>
                </div>
              ))}
            </div>
          )}
        </PremiumPanel>
      </div>
    </div>
  );
}
