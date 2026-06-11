"use client";

import { useCallback, useEffect, useState } from "react";
import { ContentStats } from "@/components/content/content-stats";
import { DevLogForm } from "@/components/content/dev-log-form";
import { PostsApprovalPanel } from "@/components/content/posts-approval-panel";
import type { StatusTab } from "@/components/content/content.constants";
import {
  computePostStats,
  fetchPosts,
  type Post,
} from "@/lib/content";
import { fetchProjects } from "@/lib/api";
import type { Project } from "@/lib/types";

export function ContentView() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [allPosts, setAllPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);

  const [statusTab, setStatusTab] = useState<StatusTab>("pending_approval");
  const [projectFilter, setProjectFilter] = useState("all");
  const [platformFilter, setPlatformFilter] = useState<string | null>(null);

  const loadPosts = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchPosts();
      setAllPosts(data);
    } catch {
      setAllPosts([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProjects().then(setProjects).catch(() => setProjects([]));
    loadPosts();
  }, [loadPosts]);

  function handlePostUpdated(updated: Post) {
    setAllPosts((prev) =>
      prev.map((p) => (p.id === updated.id ? updated : p))
    );
  }

  const stats = computePostStats(allPosts);

  return (
    <div className="space-y-6">
      <header>
        <p className="forge-heading text-[11px] text-copper/80">Studio</p>
        <h1 className="mt-1 text-2xl font-semibold tracking-wide text-ivory">
          Contenu
        </h1>
        <p className="mt-1 text-sm text-titanium">
          Dev log → posts réseaux → approbation avant publication.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-5 lg:items-start">
        <div className="space-y-6 lg:col-span-2">
          <DevLogForm
            projects={projects}
            onGenerated={loadPosts}
            onProjectsUpdated={setProjects}
          />
          <ContentStats
            pending={stats.pending}
            approvedThisWeek={stats.approvedThisWeek}
            publishedThisMonth={stats.publishedThisMonth}
          />
        </div>

        <div className="flex min-h-[520px] flex-col rounded-2xl border border-copper/10 bg-obsidian/50 p-4 ring-1 ring-white/[0.04] lg:col-span-3 lg:min-h-[640px]">
          <h2 className="mb-2 text-sm font-medium uppercase tracking-widest text-titanium">
            File d&apos;approbation
          </h2>
          <PostsApprovalPanel
            posts={allPosts}
            projects={projects}
            statusTab={statusTab}
            onStatusTabChange={setStatusTab}
            projectFilter={projectFilter}
            onProjectFilterChange={setProjectFilter}
            platformFilter={platformFilter}
            onPlatformFilterChange={setPlatformFilter}
            onPostUpdated={handlePostUpdated}
            loading={loading}
          />
        </div>
      </div>
    </div>
  );
}
