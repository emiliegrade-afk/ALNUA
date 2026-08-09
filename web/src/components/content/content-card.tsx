"use client";

import { Badge } from "@/components/ui/badge";
import { CONTENT_TYPE_LABELS, PLATFORM_STYLES } from "@/components/content/content.constants";
import type { Post } from "@/lib/content";
import { cn } from "@/lib/utils";

/* Carte Content Studio — Phase 33, ROADMAP.md. Calquée sur roadmap-card.tsx
   (même structure clic + drag). */

interface ContentCardProps {
  post: Post;
  onClick: () => void;
  isDragging?: boolean;
}

export function ContentCard({ post, onClick, isDragging }: ContentCardProps) {
  const platformStyle = PLATFORM_STYLES[post.platform];

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick();
        }
      }}
      className={cn(
        "w-full cursor-pointer rounded-xl border border-copper/15 bg-obsidian/80 p-3 text-left shadow-sm transition",
        "hover:border-copper/25 hover:bg-obsidian",
        isDragging && "rotate-1 border-copper/40 shadow-lg ring-1 ring-copper/30"
      )}
    >
      <div className="flex flex-wrap gap-1.5">
        <Badge variant="outline" className={cn("text-[10px]", platformStyle?.badge)}>
          {platformStyle?.label ?? post.platform}
        </Badge>
        <Badge variant="outline" className="border-copper/15 text-[10px] text-titanium">
          {CONTENT_TYPE_LABELS[post.content_type] ?? post.content_type}
        </Badge>
      </div>
      <p className="mt-2 line-clamp-3 text-sm leading-snug text-ivory/90">{post.text_content}</p>
    </div>
  );
}
