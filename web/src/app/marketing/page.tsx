"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AgentCard } from "@/components/shared/agent-card";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { DepartmentHeader } from "@/components/shared/department-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchPosts } from "@/lib/content";

const MARKETING_AGENTS = [
  {
    icon: "📣",
    name: "Marketing Agent",
    role: "Marketing",
    branch: "marketing" as const,
    description: "Stratégie contenu, SEO et réseaux sociaux.",
    skills: ["SEO", "Social", "Campagnes"],
  },
  {
    icon: "✍️",
    name: "Content Agent",
    role: "Support contenu",
    branch: "marketing" as const,
    description: "Rédaction posts et validation éditoriale.",
    skills: ["Copywriting", "Posts", "Dev logs"],
  },
];

export default function MarketingPage() {
  const [pendingPosts, setPendingPosts] = useState<
    Array<{ id: string; text_content: string; platform: string }>
  >([]);

  useEffect(() => {
    fetchPosts({ status: "pending" })
      .then((posts) => setPendingPosts(posts.slice(0, 10)))
      .catch(() => setPendingPosts([]));
  }, []);

  return (
    <>
      <BackToLobby />
      <DepartmentHeader
        dept="marketing"
        title="Marketing"
        subtitle="Contenu · SEO · Réseaux · Communauté"
      />

      <section className="mb-8 grid gap-4 sm:grid-cols-2">
        {MARKETING_AGENTS.map((agent) => (
          <AgentCard key={agent.name} {...agent} />
        ))}
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="border-rose-500/20 bg-[#111827]/80">
          <CardHeader>
            <CardTitle className="text-base text-white">
              Posts en attente
            </CardTitle>
            <p className="text-xs text-gray-500">
              {pendingPosts.length} post{pendingPosts.length !== 1 ? "s" : ""}{" "}
              pending
            </p>
          </CardHeader>
          <CardContent>
            {pendingPosts.length === 0 ? (
              <p className="text-sm text-gray-500">Aucun post en attente.</p>
            ) : (
              <ul className="space-y-3">
                {pendingPosts.map((post) => (
                  <li
                    key={post.id}
                    className="rounded-lg border border-white/5 p-3"
                  >
                    <span className="text-xs text-rose-400">{post.platform}</span>
                    <p className="mt-1 line-clamp-2 text-sm text-gray-300">
                      {post.text_content}
                    </p>
                  </li>
                ))}
              </ul>
            )}
            <Button asChild size="sm" variant="ghost" className="mt-4">
              <Link href="/content">Voir tout le contenu</Link>
            </Button>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card className="border-rose-500/20 bg-[#111827]/80">
            <CardHeader>
              <CardTitle className="text-base text-white">SEO</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-400">
                Dernier audit SEO via skill_seo_audit — disponible via le COO.
              </p>
              <Button asChild size="sm" variant="outline" className="mt-3 border-rose-500/30">
                <Link href="/ceo">Demander un audit SEO</Link>
              </Button>
            </CardContent>
          </Card>

          <Card className="border-rose-500/20 bg-[#111827]/80">
            <CardHeader>
              <CardTitle className="text-base text-white">Réseaux</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
              <Button asChild size="sm" variant="outline" className="border-rose-500/30">
                <a
                  href="https://discord.gg"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Discord Wyrdheim
                </a>
              </Button>
              <Button asChild size="sm" variant="outline" className="border-rose-500/30">
                <Link href="/content">Comptes sociaux</Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
}
