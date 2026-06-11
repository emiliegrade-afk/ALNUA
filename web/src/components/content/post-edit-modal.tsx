"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { updatePost, type Post } from "@/lib/content";

interface PostEditModalProps {
  post: Post | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSaved: (post: Post) => void;
}

export function PostEditModal({
  post,
  open,
  onOpenChange,
  onSaved,
}: PostEditModalProps) {
  const [text, setText] = useState("");
  const [hashtags, setHashtags] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!post) return;
    setText(post.text_content);
    setHashtags((post.hashtags ?? []).join(" "));
    const d = new Date(post.scheduled_at);
    const local = new Date(d.getTime() - d.getTimezoneOffset() * 60000)
      .toISOString()
      .slice(0, 16);
    setScheduledAt(local);
  }, [post]);

  async function handleSave() {
    if (!post) return;
    setSaving(true);
    try {
      const tagList = hashtags
        .split(/[\s,#]+/)
        .map((t) => t.replace(/^#/, "").trim())
        .filter(Boolean);
      const updated = await updatePost(post.id, {
        text_content: text.trim(),
        hashtags: tagList,
        scheduled_at: scheduledAt
          ? new Date(scheduledAt).toISOString()
          : post.scheduled_at,
      });
      toast.success("Post mis à jour");
      onSaved(updated);
      onOpenChange(false);
    } catch {
      toast.error("Erreur lors de la sauvegarde");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="border-copper/20 bg-surface-raised text-ivory/90 sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-ivory">Modifier le post</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="post-text">Texte</Label>
            <Textarea
              id="post-text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={8}
              className="border-copper/20 bg-white/[0.03]"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="post-tags">Hashtags (séparés par espaces)</Label>
            <Input
              id="post-tags"
              value={hashtags}
              onChange={(e) => setHashtags(e.target.value)}
              className="border-copper/20 bg-white/[0.03]"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="post-schedule">Publication prévue</Label>
            <Input
              id="post-schedule"
              type="datetime-local"
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
              className="border-copper/20 bg-white/[0.03]"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>
            Annuler
          </Button>
          <Button
            onClick={handleSave}
            disabled={saving || !text.trim()}
            className="bg-copper hover:bg-copper-glow"
          >
            {saving ? "Sauvegarde…" : "Sauvegarder"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
