"use client";

import { Copy, FolderOpen, X } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MarkdownContent } from "@/components/shared/markdown-content";
import { revealSummaryFile } from "@/lib/brainstorm";

export interface SummaryResult {
  summary_md: string;
  file_path: string;
  session_number: number;
  title: string;
  project_slug?: string;
}

interface SummaryResultModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  result: SummaryResult | null;
}

export function SummaryResultModal({
  open,
  onOpenChange,
  result,
}: SummaryResultModalProps) {
  if (!result) return null;

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(result!.summary_md);
      toast.success("Compte-rendu copié");
    } catch {
      toast.error("Impossible de copier");
    }
  }

  async function handleReveal() {
    try {
      await revealSummaryFile(result!.file_path);
      toast.success("Fichier ouvert dans l'explorateur");
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Impossible d'ouvrir le fichier"
      );
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[90vh] flex-col border-copper/20 bg-surface-raised sm:max-w-2xl">
        <DialogHeader>
          <p className="text-xs uppercase tracking-widest text-copper/70">
            Fiche #{String(result.session_number).padStart(3, "0")}
          </p>
          <DialogTitle className="text-xl text-ivory">{result.title}</DialogTitle>
        </DialogHeader>

        <ScrollArea className="min-h-0 flex-1 rounded-lg border border-copper/10 bg-obsidian/60 p-4">
          <MarkdownContent>{result.summary_md}</MarkdownContent>
        </ScrollArea>

        <DialogFooter className="flex shrink-0 flex-wrap gap-2 sm:justify-between">
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleCopy}
              className="border-copper/15 text-titanium"
            >
              <Copy className="mr-1.5 h-3.5 w-3.5" />
              Copier
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleReveal}
              className="border-copper/15 text-titanium"
            >
              <FolderOpen className="mr-1.5 h-3.5 w-3.5" />
              Ouvrir dans l&apos;explorateur
            </Button>
          </div>
          <Button
            type="button"
            size="sm"
            onClick={() => onOpenChange(false)}
            className="bg-copper hover:bg-copper-glow"
          >
            <X className="mr-1.5 h-3.5 w-3.5" />
            Fermer
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
