"use client";

import { useEffect, useState } from "react";
import { Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { MarkdownContent } from "@/components/shared/markdown-content";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import {
  generateWaitlistEmail,
  notifyWaitlist,
  type WaitlistStatus,
} from "@/lib/waitlist-api";
import type { Project } from "@/lib/types";

interface WaitlistNotifyModalProps {
  open: boolean;
  onClose: () => void;
  projects: Project[];
  defaultProjectId?: string;
  onSuccess: () => void;
}

export function WaitlistNotifyModal({
  open,
  onClose,
  projects,
  defaultProjectId,
  onSuccess,
}: WaitlistNotifyModalProps) {
  const [projectId, setProjectId] = useState(defaultProjectId ?? "");
  const [subject, setSubject] = useState("");
  const [messageMd, setMessageMd] = useState("");
  const [statusFilter, setStatusFilter] = useState<WaitlistStatus>("waiting");
  const [generating, setGenerating] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (open && defaultProjectId) {
      setProjectId(defaultProjectId);
    }
  }, [open, defaultProjectId]);

  const handleGenerate = async () => {
    if (!projectId) {
      toast.error("Sélectionne un projet");
      return;
    }
    setGenerating(true);
    try {
      const draft = await generateWaitlistEmail(projectId);
      setSubject(draft.subject);
      setMessageMd(draft.message_md);
      toast.success("Email généré par l'IA");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur génération");
    } finally {
      setGenerating(false);
    }
  };

  const handleSubmit = async () => {
    if (!projectId || !subject.trim() || !messageMd.trim()) {
      toast.error("Remplis tous les champs");
      return;
    }
    setSubmitting(true);
    try {
      const result = await notifyWaitlist({
        project_id: projectId,
        subject: subject.trim(),
        message_md: messageMd.trim(),
        status_filter: statusFilter,
      });
      toast.success(`${result.notified_count} inscrite(s) marquée(s) comme notifiées`);
      onSuccess();
      onClose();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-h-[90vh] overflow-y-auto border-white/10 bg-surface sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle className="text-ivory">Préparer une notification</DialogTitle>
          <DialogDescription className="text-titanium">
            Marque les inscrites comme notifiées. L&apos;envoi réel nécessite une
            intégration email (Brevo recommandé).
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-xs text-titanium">Projet</label>
              <Select value={projectId} onValueChange={setProjectId}>
                <SelectTrigger className="border-white/10">
                  <SelectValue placeholder="Choisir un projet" />
                </SelectTrigger>
                <SelectContent>
                  {projects.map((p) => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="mb-1.5 block text-xs text-titanium">
                Filtrer par statut
              </label>
              <Select
                value={statusFilter}
                onValueChange={(v) => setStatusFilter(v as WaitlistStatus)}
              >
                <SelectTrigger className="border-white/10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="waiting">En attente uniquement</SelectItem>
                  <SelectItem value="notified">Déjà notifiées</SelectItem>
                  <SelectItem value="converted">Converties</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-xs text-titanium">
              Objet de l&apos;email
            </label>
            <Input
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Bientôt : Naïa est presque prête ✨"
              className="border-white/10"
            />
          </div>

          <div>
            <div className="mb-1.5 flex items-center justify-between">
              <label className="text-xs text-titanium">Message (markdown)</label>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="h-7 gap-1 border-copper/30 text-copper-glow"
                disabled={generating || !projectId}
                onClick={handleGenerate}
              >
                {generating ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <Sparkles className="h-3 w-3" />
                )}
                Générer avec l&apos;IA
              </Button>
            </div>
            <Textarea
              value={messageMd}
              onChange={(e) => setMessageMd(e.target.value)}
              rows={6}
              placeholder="## Bonne nouvelle !&#10;&#10;On approche du lancement..."
              className="border-white/10 font-mono text-sm"
            />
          </div>

          {messageMd.trim() ? (
            <div className="rounded-lg border border-white/10 bg-obsidian/50 p-4">
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-titanium">
                Aperçu
              </p>
              <MarkdownContent>{messageMd}</MarkdownContent>
            </div>
          ) : null}
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button variant="outline" onClick={onClose}>
            Annuler
          </Button>
          <Button
            className="bg-copper text-obsidian hover:bg-copper-glow"
            disabled={submitting}
            onClick={handleSubmit}
          >
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            Valider l&apos;envoi
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
