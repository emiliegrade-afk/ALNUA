"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { ContentKanban } from "@/components/content/content-kanban";
import { PostEditModal } from "@/components/content/post-edit-modal";
import { ContentStudioCreateModal } from "@/components/content/content-studio-create-modal";
import type { CreatablePostStatus, PostStatus } from "@/components/content/content.constants";
import { fetchPosts, updatePost, type Post } from "@/lib/content";
import { fetchProjects } from "@/lib/api";
import type { Project } from "@/lib/types";
import { C } from "../app-v2/shared";

/* Onglet "Content Studio" — Phase 33, ROADMAP.md. Remplace l'ancien onglet
   "Contenu" (lecture seule) : glisser-déposer réel sur posts_queue.status
   via updatePost() (déjà existant), création manuelle par colonne. */

export function ContentStudioTab() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingPost, setEditingPost] = useState<Post | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [createDefaultStatus, setCreateDefaultStatus] = useState<CreatablePostStatus>("draft");

  async function load() {
    setLoading(true);
    try {
      const [p, proj] = await Promise.all([fetchPosts(), fetchProjects()]);
      setPosts(p);
      setProjects(proj);
    } catch {
      setPosts([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function handleStatusChange(id: string, status: PostStatus) {
    const previous = posts;
    setPosts((prev) => prev.map((p) => (p.id === id ? { ...p, status } : p)));
    try {
      await updatePost(id, { status });
    } catch (err) {
      setPosts(previous);
      toast.error(err instanceof Error ? err.message : "Erreur lors du déplacement");
    }
  }

  function openCreate(status: CreatablePostStatus) {
    setCreateDefaultStatus(status);
    setCreateOpen(true);
  }

  return (
    <div className="alnua-scroll flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto p-1">
      {loading && posts.length === 0 ? (
        <p className="text-center text-[11px]" style={{ color: C.faint }}>
          Chargement de la file de publication…
        </p>
      ) : (
        <ContentKanban
          posts={posts}
          onPostClick={setEditingPost}
          onStatusChange={handleStatusChange}
          onAddInColumn={openCreate}
        />
      )}

      <PostEditModal
        post={editingPost}
        open={Boolean(editingPost)}
        onOpenChange={(o) => !o && setEditingPost(null)}
        onSaved={(updated) => {
          setPosts((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
        }}
      />

      <ContentStudioCreateModal
        open={createOpen}
        onOpenChange={setCreateOpen}
        projects={projects}
        defaultStatus={createDefaultStatus}
        onCreated={(post) => setPosts((prev) => [post, ...prev])}
      />
    </div>
  );
}
