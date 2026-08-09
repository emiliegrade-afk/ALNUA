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
  const [reach, setReach] = useState("");
  const [engagementCount, setEngagementCount] = useState("");
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
    setReach(post.reach != null ? String(post.reach) : "");
    setEngagementCount(post.engagement_count != null ? String(post.engagement_count) : "");
  }, [post]);

  async function handleSave() {
    if (!post) return;
    setSaving(true);
    try {
      const tagList = hashtags
        .split(/[\s,#]+/)
        .map((t) => t.replace(/^#/, "").trim())
        .filter(Boolean);
      const payload: Parameters<typeof updatePost>[1] = {
        text_content: text.trim(),
        hashtags: tagList,
        scheduled_at: scheduledAt
          ? new Date(scheduledAt).toISOString()
          : post.scheduled_at,
      };
      if (reach.trim()) payload.reach = Math.max(0, parseInt(reach, 10) || 0);
      if (engagementCount.trim()) {
        payload.engagement_count = Math.max(0, parseInt(engagementCount, 10) || 0);
      }
      const updated = await updatePost(post.id, payload);
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
              className="border-copper/20 bg-obsidian-deep/50"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="post-tags">Hashtags (séparés par espaces)</Label>
            <Input
              id="post-tags"
              value={hashtags}
              onChange={(e) => setHashtags(e.target.value)}
              className="border-copper/20 bg-obsidian-deep/50"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="post-schedule">Publication prévue</Label>
            <Input
              id="post-schedule"
              type="datetime-local"
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
              className="border-copper/20 bg-obsidian-deep/50"
            />
          </div>
          {post?.status === "published" && (
            <div className="space-y-2 rounded-lg border border-copper/10 bg-obsidian-deep/40 p-3">
              <Label className="text-[11px] uppercase tracking-wide text-titanium">
                Statistiques (saisie manuelle depuis les insights de la plateforme)
              </Label>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label htmlFor="post-reach" className="text-xs">Reach</Label>
                  <Input
                    id="post-reach"
                    type="text"
                    inputMode="numeric"
                    value={reach}
                    onChange={(e) => setReach(e.target.value)}
                    placeholder="Non renseigné"
                    className="border-copper/20 bg-obsidian-deep/50"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="post-engagement" className="text-xs">Engagements</Label>
                  <Input
                    id="post-engagement"
                    type="text"
                    inputMode="numeric"
                    value={engagementCount}
                    onChange={(e) => setEngagementCount(e.target.value)}
                    placeholder="Non renseigné"
                    className="border-copper/20 bg-obsidian-deep/50"
                  />
                </div>
              </div>
              {post.stats_updated_at && (
                <p className="text-[10px] text-titanium/70">
                  Dernière mise à jour : {new Date(post.stats_updated_at).toLocaleString("fr-FR")}
                </p>
              )}
            </div>
          )}
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
