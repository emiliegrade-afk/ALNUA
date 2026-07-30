"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import Link from "next/link";
import { BureauPage } from "@/components/shared/bureau-page";
import { BureauPanel } from "@/components/shared/bureau-panel";
import { DepartmentWorkspace } from "@/components/shared/department-workspace";
import { Button } from "@/components/ui/button";
import { fetchPosts } from "@/lib/content";

const MarketingConsole = dynamic(
  () =>
    import("@/components/marketing/marketing-console").then((m) => ({
      default: m.MarketingConsole,
    })),
  {
    loading: () => (
      <p className="text-sm text-titane/60">Chargement console marketing…</p>
    ),
  },
);

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
    <BureauPage
      dept="marketing"
      bureau="marketing"
      title="Marketing"
      subtitle="Lena · Eliot · Contenu · SEO · Réseaux"
    >
      <DepartmentWorkspace bureau="marketing" dept="marketing" projectBranch={null} />

      <BureauPanel title="Posts en attente">
        <p className="label-caps mb-4">
          {pendingPosts.length} post{pendingPosts.length !== 1 ? "s" : ""} pending
        </p>
        {pendingPosts.length === 0 ? (
          <p className="font-body text-sm text-titane/60">Aucun post en attente.</p>
        ) : (
          <ul className="space-y-3">
            {pendingPosts.map((post) => (
              <li
                key={post.id}
                className="rounded-lg border border-bronze-faint bg-obsidian-deep/50 p-3"
              >
                <span className="font-body text-xs text-bronze-bright">{post.platform}</span>
                <p className="mt-1 line-clamp-2 font-body text-sm text-ivoire/85">
                  {post.text_content}
                </p>
              </li>
            ))}
          </ul>
        )}
        <Button asChild size="sm" variant="ghost" className="mt-4 text-bronze-bright">
          <Link href="/content">Voir tout le contenu</Link>
        </Button>
      </BureauPanel>

      <MarketingConsole />
    </BureauPage>
  );
}
