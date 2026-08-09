"use client";

import { useEffect, useState } from "react";
import { fetchPosts, type Post } from "@/lib/content";
import { fetchProjects } from "@/lib/api";
import type { Project } from "@/lib/types";
import { PerformanceByPlatformPanel } from "@/components/marketing/performance-by-platform-panel";
import { TopContentPanel } from "@/components/marketing/top-content-panel";
import { ConversionFunnelPanel } from "@/components/marketing/conversion-funnel-panel";
import { C } from "../app-v2/shared";

/* Onglet "Analytics" — Phase 38, ROADMAP.md. Vue dédiée et élargie des
   panneaux de mesure réelle introduits Phase 37 (Performances par canal,
   Top contenus, Entonnoir de conversion) — la Vue Globale garde une version
   condensée de ces mêmes panneaux pour l'aperçu quotidien, ici c'est la
   vue complète pour l'analyse. Pas de nouvelle donnée fabriquée : mêmes
   sources, mêmes composants, juste plus d'espace. */

export function AnalyticsTab() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchPosts(), fetchProjects()])
      .then(([p, proj]) => {
        if (!cancelled) {
          setPosts(p);
          setProjects(proj);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setPosts([]);
          setProjects([]);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="alnua-scroll flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto p-1">
      {loading && posts.length === 0 ? (
        <p className="text-center text-[11px]" style={{ color: C.faint }}>
          Chargement…
        </p>
      ) : (
        <div className="grid gap-3 lg:grid-cols-2">
          <PerformanceByPlatformPanel />
          <ConversionFunnelPanel projects={projects} />
          <div className="lg:col-span-2">
            <TopContentPanel posts={posts} />
          </div>
        </div>
      )}
    </div>
  );
}
