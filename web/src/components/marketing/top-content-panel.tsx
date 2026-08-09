"use client";

import { PLATFORM_STYLES } from "@/components/content/content.constants";
import type { Post } from "@/lib/content";
import { C } from "@/app/app-v2/shared";
import { PremiumPanel, PlatformBadge, MONO } from "@/app/marketing-v2/premium";

/* "Top contenus" — Phase 37, ROADMAP.md. Classe les posts publiés par reach
   réel, saisi manuellement post-publication (Content Studio → ouvrir un post
   publié → section Statistiques). Pas de % de reach affiché (contrairement
   à la maquette d'origine) : ça supposerait une audience totale connue par
   plateforme, qu'on ne suit pas — un vrai nombre plutôt qu'un taux inventé. */

export function TopContentPanel({ posts }: { posts: Post[] }) {
  const ranked = posts
    .filter((p) => p.status === "published" && p.reach != null)
    .sort((a, b) => (b.reach ?? 0) - (a.reach ?? 0))
    .slice(0, 5);

  return (
    <PremiumPanel title="Top contenus">
      {ranked.length === 0 ? (
        <p className="text-[11px] leading-relaxed" style={{ color: C.faint }}>
          Aucune statistique de contenu saisie pour l&apos;instant. Ouvre un post publié dans
          Content Studio pour renseigner son reach/engagements.
        </p>
      ) : (
        <div className="flex flex-col">
          {ranked.map((post, i) => (
            <div key={post.id} className="flex items-center gap-3 border-b py-2.5 last:border-none last:pb-0" style={{ borderColor: C.line }}>
              <span className="w-4 shrink-0 text-center text-[11px] tabular-nums" style={{ color: C.faint, fontFamily: MONO }}>
                {i + 1}
              </span>
              <PlatformBadge platform={post.platform} size={36} />
              <div className="min-w-0 flex-1">
                <p className="truncate text-[12px]" style={{ color: C.ivory }}>
                  {post.text_content}
                </p>
                <p className="mt-0.5 text-[10px]" style={{ color: C.faint }}>
                  {PLATFORM_STYLES[post.platform]?.label ?? post.platform}
                  {post.engagement_count != null ? ` · ${post.engagement_count.toLocaleString("fr-FR")} engagements` : ""}
                </p>
              </div>
              <span className="shrink-0 text-[15px] font-semibold tabular-nums" style={{ color: C.copperLight, fontFamily: MONO }}>
                {post.reach!.toLocaleString("fr-FR")}
              </span>
            </div>
          ))}
        </div>
      )}
    </PremiumPanel>
  );
}
