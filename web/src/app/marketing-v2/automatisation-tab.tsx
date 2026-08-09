"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchEventStats, fetchRecentEvents, type EventStats, type HubEvent } from "@/lib/admin-events-api";
import { fetchPosts, type Post } from "@/lib/content";
import { getAgentsForBureau } from "@/lib/agent-bureau";
import { PremiumPanel, PremiumKpiTile } from "./premium";
import { C } from "../app-v2/shared";

/* Onglet "Automatisation" — Phase 38, ROADMAP.md. Le Hub a un vrai bus
   d'événements (services/event_bus.py) et un vrai pipeline de contenu
   (posts_queue) — cet onglet en montre l'état réel plutôt qu'un tableau de
   bord d'automatisations marketing qui n'existe pas (pas de Zapier/Make
   branché). Filtré aux événements émis par des agents du bureau Marketing
   quand c'est identifiable ; sinon flux global du Hub, étiqueté comme tel. */

export function AutomatisationTab() {
  const [events, setEvents] = useState<HubEvent[]>([]);
  const [stats, setStats] = useState<EventStats | null>(null);
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchRecentEvents({ limit: 30 }), fetchEventStats(), fetchPosts()])
      .then(([ev, st, p]) => {
        if (!cancelled) {
          setEvents(ev);
          setStats(st);
          setPosts(p);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setEvents([]);
          setStats(null);
          setPosts([]);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const marketingAgentIds = useMemo(
    () => new Set(getAgentsForBureau("marketing").map((a) => a.id)),
    []
  );
  const marketingEvents = events.filter((e) => marketingAgentIds.has(e.source_agent));

  const pipelineCounts = useMemo(
    () => ({
      draft: posts.filter((p) => p.status === "draft").length,
      pending: posts.filter((p) => p.status === "pending_approval").length,
      approved: posts.filter((p) => p.status === "approved").length,
      scheduled: posts.filter((p) => p.status === "approved" && new Date(p.scheduled_at) > new Date()).length,
    }),
    [posts]
  );

  return (
    <div className="alnua-scroll flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto p-1">
      {loading ? (
        <p className="text-center text-[11px]" style={{ color: C.faint }}>
          Chargement…
        </p>
      ) : (
        <>
          <div className="flex flex-wrap gap-3">
            <PremiumKpiTile label="EN BROUILLON" value={pipelineCounts.draft} caption="posts_queue" />
            <PremiumKpiTile label="À APPROUVER" value={pipelineCounts.pending} caption="file d'attente" />
            <PremiumKpiTile label="APPROUVÉS" value={pipelineCounts.approved} caption="prêts à publier" />
            <PremiumKpiTile label="PROGRAMMÉS" value={pipelineCounts.scheduled} caption="date future" />
            <PremiumKpiTile
              label="ÉVÉNEMENTS EN MÉMOIRE"
              value={stats?.total_events_in_memory ?? "—"}
              caption="bus d'événements, tout le Hub"
            />
          </div>

          <PremiumPanel title="Activité du bus d'événements — équipe Marketing">
            {marketingEvents.length === 0 ? (
              <p className="text-[11px] leading-relaxed" style={{ color: C.faint }}>
                Aucun événement récent émis par un agent Marketing. Le bus (
                <code>services/event_bus.py</code>) est actif pour tout le Hub — voir le flux
                global dans Réglages → Événements si besoin.
              </p>
            ) : (
              <div className="flex flex-col gap-2">
                {marketingEvents.slice(0, 12).map((e) => (
                  <div key={e.event_id} className="flex items-center justify-between gap-3 border-b pb-2 text-[11px]" style={{ borderColor: C.line }}>
                    <span style={{ color: C.warm }}>{e.event_type}</span>
                    <span style={{ color: C.faint }}>{e.source_agent}</span>
                    <span style={{ color: C.faint }}>{new Date(e.ts * 1000).toLocaleTimeString("fr-FR")}</span>
                  </div>
                ))}
              </div>
            )}
          </PremiumPanel>
        </>
      )}
    </div>
  );
}
