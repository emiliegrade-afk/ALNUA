"use client";

import { useState } from "react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import {
  Check,
  ChevronDown,
  ChevronUp,
  Copy,
  Pencil,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  CONTENT_TYPE_LABELS,
  PLATFORM_STYLES,
  projectBadgeClass,
} from "@/components/content/content.constants";
import { updatePost, type Post } from "@/lib/content";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";

interface PostCardProps {
  post: Post;
  project?: Project;
  onUpdated: (post: Post) => void;
  onEdit: (post: Post) => void;
}

function CollapsibleBlock({
  title,
  content,
}: {
  title: string;
  content: string;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-lg border border-copper/10 bg-obsidian-deep/40">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-3 py-2 text-left text-xs text-titanium hover:text-ivory"
      >
        {title}
        {open ? (
          <ChevronUp className="h-3.5 w-3.5" />
        ) : (
          <ChevronDown className="h-3.5 w-3.5" />
        )}
      </button>
      {open && (
        <div className="border-t border-copper/10 px-3 py-2">
          <p className="whitespace-pre-wrap text-xs leading-relaxed text-ivory/75">
            {content}
          </p>
          <Button
            type="button"
            variant="ghost"
            size="xs"
            className="mt-2 h-6 text-[10px]"
            onClick={() => {
              navigator.clipboard.writeText(content);
              toast.success("Copié");
            }}
          >
            <Copy className="mr-1 h-3 w-3" />
            Copier
          </Button>
        </div>
      )}
    </div>
  );
}

export function PostCard({ post, project, onUpdated, onEdit }: PostCardProps) {
  const [loading, setLoading] = useState<string | null>(null);
  const platformStyle = PLATFORM_STYLES[post.platform];

  async function setStatus(status: "approved" | "rejected") {
    setLoading(status);
    try {
      const updated = await updatePost(post.id, { status });
      toast.success(status === "approved" ? "Post approuvé" : "Post rejeté");
      onUpdated(updated);
    } catch {
      toast.error("Action impossible");
    } finally {
      setLoading(null);
    }
  }

  return (
    <Card className="border-copper/15 bg-surface/80 ring-1 ring-copper/10">
      <CardContent className="space-y-3 p-4">
        <div className="flex flex-wrap gap-1.5">
          <Badge
            variant="outline"
            className={cn("ring-1", platformStyle.badge)}
          >
            {platformStyle.label}
          </Badge>
          {project && (
            <Badge
              variant="outline"
              className={cn("ring-1", projectBadgeClass(project.branch))}
            >
              {project.name}
            </Badge>
          )}
          <Badge variant="secondary" className="bg-obsidian-deep/50 text-titanium">
            {CONTENT_TYPE_LABELS[post.content_type] ?? post.content_type}
          </Badge>
        </div>

        <div className="max-h-48 overflow-y-auto rounded-lg bg-obsidian-deep/40 p-3 text-sm leading-relaxed text-ivory/85 whitespace-pre-wrap">
          {post.text_content}
        </div>

        {(post.hashtags?.length ?? 0) > 0 && (
          <div className="flex flex-wrap gap-1">
            {post.hashtags.map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-violet-500/10 px-2 py-0.5 text-[10px] text-violet-300/90"
              >
                #{tag.replace(/^#/, "")}
              </span>
            ))}
          </div>
        )}

        <div className="flex flex-wrap gap-3 text-[11px] text-titanium/80">
          <span>
            Créé{" "}
            {format(new Date(post.created_at), "d MMM yyyy HH:mm", {
              locale: fr,
            })}
          </span>
          <span>
            Prévu{" "}
            {format(new Date(post.scheduled_at), "d MMM yyyy HH:mm", {
              locale: fr,
            })}
          </span>
        </div>

        {post.image_prompt && (
          <CollapsibleBlock title="Prompt image" content={post.image_prompt} />
        )}
        {post.video_script && (
          <CollapsibleBlock title="Script vidéo" content={post.video_script} />
        )}

        {post.status === "pending_approval" && (
          <div className="flex flex-wrap gap-2 pt-1">
            <Button
              size="sm"
              disabled={!!loading}
              onClick={() => setStatus("approved")}
              className="bg-emerald-600/90 hover:bg-emerald-500"
            >
              <Check className="mr-1 h-3.5 w-3.5" />
              {loading === "approved" ? "…" : "Approuver"}
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={!!loading}
              onClick={() => onEdit(post)}
              className="border-copper/15 bg-obsidian-deep/50"
            >
              <Pencil className="mr-1 h-3.5 w-3.5" />
              Modifier
            </Button>
            <Button
              size="sm"
              variant="ghost"
              disabled={!!loading}
              onClick={() => setStatus("rejected")}
              className="text-red-400/80 hover:bg-red-500/10 hover:text-red-300"
            >
              <Trash2 className="mr-1 h-3.5 w-3.5" />
              {loading === "rejected" ? "…" : "Rejeter"}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
