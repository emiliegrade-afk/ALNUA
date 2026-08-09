"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchPosts, type Post } from "@/lib/content";
import { PLATFORMS } from "@/components/content/content.constants";
import { PremiumPanel, PlatformBadge, MONO } from "./premium";
import { C } from "../app-v2/shared";

/* Onglet "Social Media" — Phase 38, ROADMAP.md. Contenu organique groupé
   par plateforme (posts_queue), avec reach/engagement réels là où ils ont
   été saisis (Phase 37). Distinct de "Campagnes" (publicité payante) et de
   "Content Studio" (gestion du pipeline de production) : ici, une vue
   consolidée par canal — ce qui correspond à la maquette d'Emilie sans
   dupliquer les deux autres onglets. */

export function SocialMediaTab() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchPosts()
      .then((p) => {
        if (!cancelled) setPosts(p);
      })
      .catch(() => {
        if (!cancelled) setPosts([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const byPlatform = useMemo(() => {
    return PLATFORMS.map((p) => {
      const platformPosts = posts.filter((post) => post.platform === p.id);
      const published = platformPosts.filter((post) => post.status === "published");
      const withReach = published.filter((post) => post.reach != null);
      const totalReach = withReach.reduce((sum, post) => sum + (post.reach ?? 0), 0);
      const totalEngagement = published
        .filter((post) => post.engagement_count != null)
        .reduce((sum, post) => sum + (post.engagement_count ?? 0), 0);
      return {
        ...p,
        total: platformPosts.length,
        published: published.length,
        avgReach: withReach.length > 0 ? Math.round(totalReach / withReach.length) : null,
        totalEngagement,
        statsCount: withReach.length,
        recent: published
          .slice()
          .sort((a, b) => (b.published_at ?? "").localeCompare(a.published_at ?? ""))
          .slice(0, 3),
      };
    }).filter((p) => p.total > 0);
  }, [posts]);

  return (
    <div className="alnua-scroll flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto p-1">
      {loading && posts.length === 0 ? (
        <p className="text-center text-[11px]" style={{ color: C.faint }}>
          Chargement…
        </p>
      ) : byPlatform.length === 0 ? (
        <p className="text-center text-[11px]" style={{ color: C.faint }}>
          Aucun post pour l&apos;instant.
        </p>
      ) : (
        <div className="grid gap-3 lg:grid-cols-2 xl:grid-cols-3">
          {byPlatform.map((p) => (
            <PremiumPanel key={p.id}>
              <div className="flex items-center gap-3">
                <PlatformBadge platform={p.id} size={38} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[13px] font-semibold" style={{ color: C.ivory }}>
                    {p.label}
                  </p>
                  <p className="text-[10px]" style={{ color: C.faint }}>
                    {p.published} publié{p.published > 1 ? "s" : ""} · {p.total} au total
                  </p>
                </div>
              </div>

              <div className="mt-3.5 grid grid-cols-2 gap-3">
                <div>
                  <p className="text-[19px] font-semibold" style={{ fontFamily: MONO, color: C.ivory }}>
                    {p.avgReach != null ? p.avgReach.toLocaleString("fr-FR") : "—"}
                  </p>
                  <p className="text-[9.5px]" style={{ color: C.faint }}>
                    Reach moyen {p.statsCount > 0 ? `(${p.statsCount} post${p.statsCount > 1 ? "s" : ""} suivis)` : "(aucune stat saisie)"}
                  </p>
                </div>
                <div>
                  <p className="text-[19px] font-semibold" style={{ fontFamily: MONO, color: C.ivory }}>
                    {p.totalEngagement > 0 ? p.totalEngagement.toLocaleString("fr-FR") : "—"}
                  </p>
                  <p className="text-[9.5px]" style={{ color: C.faint }}>
                    Engagements cumulés
                  </p>
                </div>
              </div>

              {p.recent.length > 0 ? (
                <div className="mt-3.5 flex flex-col gap-1.5 border-t pt-3" style={{ borderColor: C.line }}>
                  {p.recent.map((post) => (
                    <p key={post.id} className="truncate text-[10.5px]" style={{ color: C.muted }}>
                      {post.text_content}
                    </p>
                  ))}
                </div>
              ) : null}
            </PremiumPanel>
          ))}
        </div>
      )}
    </div>
  );
}
