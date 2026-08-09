"use client";

import { useCallback, useEffect, useState } from "react";
import { ContentCalendar } from "@/components/content/content-calendar";
import { ContentStats } from "@/components/content/content-stats";
import { DevLogForm } from "@/components/content/dev-log-form";
import { PostComposer } from "@/components/content/post-composer";
import { PostsApprovalPanel } from "@/components/content/posts-approval-panel";
import type { ContentSector, StatusTab } from "@/components/content/content.constants";
import {
  computePostStats,
  fetchPosts,
  type Post,
} from "@/lib/content";
import { fetchProjects } from "@/lib/api";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";

type StudioTab = "queue" | "calendar" | "composer";

const STUDIO_TABS: { id: StudioTab; label: string }[] = [
  { id: "queue", label: "File d'approbation" },
  { id: "calendar", label: "Calendrier" },
  { id: "composer", label: "Composer" },
];

export function ContentView() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [allPosts, setAllPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);

  const [studioTab, setStudioTab] = useState<StudioTab>("queue");
  const [statusTab, setStatusTab] = useState<StatusTab>("pending_approval");
  const [projectFilter, setProjectFilter] = useState("all");
  const [platformFilter, setPlatformFilter] = useState<string | null>(null);
  const [sectorFilter, setSectorFilter] = useState<ContentSector | null>(null);

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

  function handlePostsCreated(created: Post[]) {
    setAllPosts((prev) => [...created, ...prev]);
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
          Dev log → posts réseaux → calendrier → approbation avant publication.
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
            posts={allPosts}
          />
        </div>

        <div className="flex min-h-[520px] flex-col rounded-2xl border border-copper/10 bg-obsidian/50 p-4 ring-1 ring-copper/10 lg:col-span-3 lg:min-h-[640px]">
          <div className="mb-4 flex flex-wrap gap-1.5 border-b border-copper/10 pb-3">
            {STUDIO_TABS.map(({ id, label }) => (
              <button
                key={id}
                type="button"
                onClick={() => setStudioTab(id)}
                className={cn(
                  "rounded-lg border px-3 py-1.5 text-xs transition",
                  studioTab === id
                    ? "border-copper/45 bg-copper/10 text-copper-glow"
                    : "border-transparent text-titanium hover:border-copper/20 hover:bg-obsidian-deep/50"
                )}
              >
                {label}
              </button>
            ))}
          </div>

          {studioTab === "queue" && (
            <PostsApprovalPanel
              posts={allPosts}
              projects={projects}
              statusTab={statusTab}
              onStatusTabChange={setStatusTab}
              projectFilter={projectFilter}
              onProjectFilterChange={setProjectFilter}
              platformFilter={platformFilter}
              onPlatformFilterChange={setPlatformFilter}
              sectorFilter={sectorFilter}
              onSectorFilterChange={setSectorFilter}
              onPostUpdated={handlePostUpdated}
              loading={loading}
            />
          )}

          {studioTab === "calendar" && (
            <ContentCalendar onPostUpdated={handlePostUpdated} />
          )}

          {studioTab === "composer" && (
            <PostComposer
              projects={projects}
              onProjectsUpdated={setProjects}
              onCreated={handlePostsCreated}
            />
          )}
        </div>
      </div>
    </div>
  );
}
