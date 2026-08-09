"use client";

import { ChevronRight, Plus } from "lucide-react";
import { DragDropContext, Droppable, Draggable, type DropResult } from "@hello-pangea/dnd";
import { ContentCard } from "@/components/content/content-card";
import {
  CONTENT_TYPE_LABELS,
  CONTENT_STUDIO_COLUMNS,
  PLATFORM_STYLES,
  POST_STATUS_LABELS,
} from "@/components/content/content.constants";
import type { Post } from "@/lib/content";
import type { CreatablePostStatus, PostStatus } from "@/components/content/content.constants";
import { cn } from "@/lib/utils";

/* Content Studio Kanban — Phase 33, ROADMAP.md. Calqué sur
   roadmap-kanban.tsx (@hello-pangea/dnd). 4 colonnes draggables seulement
   (draft/pending_approval/approved/published) : rejected/failed sont
   produits par le pipeline automatique (publisher bot), pas par un
   déplacement humain — un glisser-déposer direct vers "published" laisserait
   published_at à NULL et fausserait computePostStats (content.ts). Affichés
   en lecture seule dans un panneau replié séparé. */

interface ContentKanbanProps {
  posts: Post[];
  onPostClick: (post: Post) => void;
  onStatusChange: (id: string, status: PostStatus) => void;
  onAddInColumn: (status: CreatablePostStatus) => void;
}

export function ContentKanban({
  posts,
  onPostClick,
  onStatusChange,
  onAddInColumn,
}: ContentKanbanProps) {
  const readOnlyPosts = posts.filter((p) => p.status === "rejected" || p.status === "failed");

  function handleDragEnd(result: DropResult) {
    const { destination, source, draggableId } = result;
    if (!destination) return;
    if (destination.droppableId === source.droppableId && destination.index === source.index) {
      return;
    }
    const newStatus = destination.droppableId as PostStatus;
    const post = posts.find((p) => p.id === draggableId);
    if (post && post.status !== newStatus) {
      onStatusChange(draggableId, newStatus);
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <DragDropContext onDragEnd={handleDragEnd}>
        <div className="overflow-x-auto pb-2">
          <div className="grid min-w-[min(100%,280px)] grid-cols-1 gap-4 sm:min-w-[560px] sm:grid-cols-2 xl:min-w-[1100px] xl:grid-cols-4">
            {CONTENT_STUDIO_COLUMNS.map((col) => {
              const columnPosts = posts.filter((p) => p.status === col.id);
              return (
                <div
                  key={col.id}
                  className="flex min-h-[420px] flex-col rounded-2xl border border-copper/10 bg-obsidian/40 ring-1 ring-copper/10"
                >
                  <div className="flex items-center justify-between border-b border-copper/10 px-3 py-2.5">
                    <h3 className="text-sm font-medium text-ivory">
                      <span className="mr-1.5">{col.emoji}</span>
                      {col.label}
                    </h3>
                    <span className="rounded-full bg-obsidian-deep/50 px-2 py-0.5 text-[11px] text-titanium">
                      {columnPosts.length}
                    </span>
                  </div>

                  <Droppable droppableId={col.id}>
                    {(provided, snapshot) => (
                      <div
                        ref={provided.innerRef}
                        {...provided.droppableProps}
                        className={cn(
                          "flex flex-1 flex-col gap-2 p-2 transition-colors",
                          snapshot.isDraggingOver && "bg-copper/5"
                        )}
                      >
                        {columnPosts.map((post, index) => (
                          <Draggable key={post.id} draggableId={post.id} index={index}>
                            {(dragProvided, dragSnapshot) => {
                              const { style, ...draggableProps } = dragProvided.draggableProps;
                              return (
                                <div
                                  ref={dragProvided.innerRef}
                                  {...draggableProps}
                                  {...dragProvided.dragHandleProps}
                                  style={style as React.CSSProperties | undefined}
                                >
                                  <ContentCard
                                    post={post}
                                    onClick={() => onPostClick(post)}
                                    isDragging={dragSnapshot.isDragging}
                                  />
                                </div>
                              );
                            }}
                          </Draggable>
                        ))}
                        {provided.placeholder}
                      </div>
                    )}
                  </Droppable>

                  {col.id !== "published" ? (
                    <button
                      type="button"
                      onClick={() => onAddInColumn(col.id as CreatablePostStatus)}
                      className="m-2 flex items-center justify-center gap-1 rounded-lg border border-dashed border-copper/15 py-2 text-xs text-titanium transition hover:border-copper/30 hover:text-copper-glow"
                    >
                      <Plus className="h-3.5 w-3.5" />
                      Ajouter
                    </button>
                  ) : null}
                </div>
              );
            })}
          </div>
        </div>
      </DragDropContext>

      {readOnlyPosts.length > 0 ? (
        <details className="group rounded-xl border border-copper/10">
          <summary className="flex cursor-pointer items-center gap-2 px-4 py-2.5 text-[10.5px] text-titanium">
            <ChevronRight className="h-3.5 w-3.5 transition-transform group-open:rotate-90" />
            Rejetés / échoués (lecture seule — {readOnlyPosts.length})
          </summary>
          <div className="grid gap-2 border-t border-copper/10 p-3 sm:grid-cols-2 xl:grid-cols-3">
            {readOnlyPosts.map((post) => (
              <div
                key={post.id}
                className="rounded-lg border border-copper/10 bg-obsidian/60 p-2.5 opacity-70"
              >
                <div className="flex items-center gap-1.5 text-[9px] text-titanium/70">
                  <span>{PLATFORM_STYLES[post.platform]?.label ?? post.platform}</span>
                  <span>·</span>
                  <span>{CONTENT_TYPE_LABELS[post.content_type] ?? post.content_type}</span>
                  <span>·</span>
                  <span>{POST_STATUS_LABELS[post.status]}</span>
                </div>
                <p className="mt-1 line-clamp-2 text-[11px] text-ivory/70">{post.text_content}</p>
              </div>
            ))}
          </div>
        </details>
      ) : null}
    </div>
  );
}
