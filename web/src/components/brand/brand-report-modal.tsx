"use client";

import { FileText } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MarkdownContent } from "@/components/shared/markdown-content";

interface BrandReportModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  brandName: string;
  reportMarkdown: string | null;
  loading?: boolean;
}

export function BrandReportModal({
  open,
  onOpenChange,
  brandName,
  reportMarkdown,
  loading = false,
}: BrandReportModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[90vh] flex-col border-copper/20 bg-surface-raised sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-ivory">
            <FileText className="h-5 w-5 text-copper" />
            Brand Report — {brandName}
          </DialogTitle>
        </DialogHeader>

        <ScrollArea className="max-h-[70vh] flex-1 pr-3">
          {loading && (
            <p className="text-sm italic text-titanium/60">
              Chargement du rapport…
            </p>
          )}
          {!loading && reportMarkdown && (
            <MarkdownContent>{reportMarkdown}</MarkdownContent>
          )}
          {!loading && !reportMarkdown && (
            <p className="text-sm text-titanium/70">
              Rapport non disponible. Génère d&apos;abord le kit complet.
            </p>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
