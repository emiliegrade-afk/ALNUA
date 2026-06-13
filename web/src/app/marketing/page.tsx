"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { BureauAgentsSection } from "@/components/shared/bureau-agents-section";
import { DepartmentHeader } from "@/components/shared/department-header";
import { MarketingConsole } from "@/components/marketing/marketing-console";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchPosts } from "@/lib/content";

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
        subtitle="Lena · Eliot · Contenu · SEO · Réseaux"
      />

      <BureauAgentsSection bureau="marketing" />

      <div className="mb-8">
        <Card className="border-copper/20 bg-obsidian-2/90">
          <CardHeader>
            <CardTitle className="font-title text-base text-ivory">Posts en attente</CardTitle>
            <p className="label-caps">
              {pendingPosts.length} post{pendingPosts.length !== 1 ? "s" : ""} pending
            </p>
          </CardHeader>
          <CardContent>
            {pendingPosts.length === 0 ? (
              <p className="font-body text-sm text-titanium/60">Aucun post en attente.</p>
            ) : (
              <ul className="space-y-3">
                {pendingPosts.map((post) => (
                  <li key={post.id} className="rounded-lg border border-copper/10 p-3">
                    <span className="font-body text-xs text-copper">{post.platform}</span>
                    <p className="mt-1 line-clamp-2 font-body text-sm text-ivory/80">
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
      </div>

      <MarketingConsole />
    </>
  );
}
