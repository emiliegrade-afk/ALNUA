"use client";

import { ArrowLeft } from "lucide-react";
import {
  PLATFORMS,
  PLATFORM_STYLES,
  SECTORS,
  SECTOR_STYLES,
  STATUS_TABS,
  type ContentSector,
  type StatusTab,
} from "@/components/content/content.constants";
import { PostCard } from "@/components/content/post-card";
import { PostEditModal } from "@/components/content/post-edit-modal";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Post } from "@/lib/content";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useState } from "react";

interface PostsApprovalPanelProps {
  posts: Post[];
  projects: Project[];
  statusTab: StatusTab;
  onStatusTabChange: (tab: StatusTab) => void;
  projectFilter: string;
  onProjectFilterChange: (id: string) => void;
  platformFilter: string | null;
  onPlatformFilterChange: (platform: string | null) => void;
  sectorFilter: ContentSector | null;
  onSectorFilterChange: (sector: ContentSector | null) => void;
  onPostUpdated: (post: Post) => void;
  loading?: boolean;
}

export function PostsApprovalPanel({
  posts,
  projects,
  statusTab,
  onStatusTabChange,
  projectFilter,
  onProjectFilterChange,
  platformFilter,
  onPlatformFilterChange,
  sectorFilter,
  onSectorFilterChange,
  onPostUpdated,
  loading,
}: PostsApprovalPanelProps) {
  const [editingPost, setEditingPost] = useState<Post | null>(null);

  const projectMap = Object.fromEntries(projects.map((p) => [p.id, p]));

  const filtered = posts.filter((p) => {
    if (statusTab !== "all" && p.status !== statusTab) return false;
    if (projectFilter !== "all" && p.project_id !== projectFilter) return false;
    if (platformFilter && p.platform !== platformFilter) return false;
    if (sectorFilter && p.sector !== sectorFilter) return false;
    return true;
  });

  const showEmptyPending =
    statusTab === "pending_approval" &&
    !loading &&
    filtered.length === 0 &&
    !platformFilter &&
    projectFilter === "all";

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="mb-4 space-y-3">
        <div className="flex flex-wrap gap-1.5">
          {STATUS_TABS.map(({ id, label }) => (
            <button
              key={id}
              type="button"
              onClick={() => onStatusTabChange(id)}
              className={cn(
                "rounded-lg border px-3 py-1.5 text-xs transition",
                statusTab === id
                  ? "border-copper/45 bg-copper/10 text-copper-glow"
                  : "border-transparent text-titanium hover:border-copper/20 hover:bg-obsidian-deep/50"
              )}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Select value={projectFilter} onValueChange={onProjectFilterChange}>
            <SelectTrigger className="h-8 w-[160px] border-copper/20 bg-obsidian-deep/50 text-xs">
              <SelectValue placeholder="Projet" />
            </SelectTrigger>
            <SelectContent className="border-copper/20 bg-surface-raised">
              <SelectItem value="all">Tous les projets</SelectItem>
              {projects.map((p) => (
                <SelectItem key={p.id} value={p.id}>
                  {p.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <div className="flex flex-wrap gap-1">
            {PLATFORMS.map(({ id }) => {
              const style = PLATFORM_STYLES[id];
              const active = platformFilter === id;
              return (
                <button
                  key={id}
                  type="button"
                  title={style.label}
                  onClick={() =>
                    onPlatformFilterChange(active ? null : id)
                  }
                  className={cn(
                    "rounded-md px-2 py-1 text-[10px] ring-1 transition",
                    active
                      ? style.badge
                      : "bg-obsidian-deep/50 text-titanium ring-copper/15 hover:ring-copper/20"
                  )}
                >
                  {style.label}
                </button>
              );
            })}
          </div>

          <div className="flex flex-wrap gap-1">
            {SECTORS.map(({ id, label }) => {
              const active = sectorFilter === id;
              return (
                <button
                  key={id}
                  type="button"
                  title={label}
                  onClick={() => onSectorFilterChange(active ? null : id)}
                  className={cn(
                    "rounded-md px-2 py-1 text-[10px] ring-1 transition",
                    active
                      ? SECTOR_STYLES[id]
                      : "bg-obsidian-deep/50 text-titanium ring-copper/15 hover:ring-copper/20"
                  )}
                >
                  {label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {loading ? (
        <p className="py-12 text-center text-sm text-titanium">
          Chargement des posts…
        </p>
      ) : showEmptyPending ? (
        <div className="flex flex-1 flex-col items-center justify-center py-12 text-center">
          <p className="max-w-sm text-sm text-titanium">
            Aucun post en attente — note ce que tu as buildé et génère du
            contenu ✨
          </p>
          <div className="mt-4 flex items-center gap-2 text-xs text-copper/70">
            <ArrowLeft className="h-4 w-4" />
            <span>Commence par le Dev Log</span>
          </div>
        </div>
      ) : filtered.length === 0 ? (
        <p className="py-12 text-center text-sm text-titanium">
          Aucun post pour ces filtres.
        </p>
      ) : (
        <div className="space-y-3 overflow-y-auto pr-1">
          {filtered.map((post) => (
            <PostCard
              key={post.id}
              post={post}
              project={projectMap[post.project_id]}
              onUpdated={onPostUpdated}
              onEdit={setEditingPost}
            />
          ))}
        </div>
      )}

      <PostEditModal
        post={editingPost}
        open={!!editingPost}
        onOpenChange={(open) => !open && setEditingPost(null)}
        onSaved={onPostUpdated}
      />
    </div>
  );
}
