"use client";

import { format } from "date-fns";
import { fr } from "date-fns/locale";
import Link from "next/link";
import { ExternalLink, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  BETA_TYPE_LABELS,
  severityStyle,
} from "@/components/beta/beta.constants";
import type { BetaFeedback } from "@/lib/beta-api";
import { ticketHref } from "@/lib/routes";
import { cn } from "@/lib/utils";

interface BetaFeedbackDetailPanelProps {
  feedback: BetaFeedback | null;
  open: boolean;
  onClose: () => void;
}

export function BetaFeedbackDetailPanel({
  feedback,
  open,
  onClose,
}: BetaFeedbackDetailPanelProps) {
  if (!open || !feedback) return null;

  return (
    <>
      <button
        type="button"
        aria-label="Fermer"
        className="fixed inset-0 z-40 bg-obsidian/85 backdrop-blur-sm"
        onClick={onClose}
      />
      <aside
        className={cn(
          "fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col border-l border-copper/15 bg-surface shadow-2xl",
          "animate-fade-in"
        )}
      >
        <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
          <h2 className="text-sm font-semibold text-ivory">Détail feedback</h2>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Fermer">
            <X className="h-4 w-4" />
          </Button>
        </div>

        <ScrollArea className="flex-1 px-5 py-4">
          <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline" className={severityStyle(feedback.severity)}>
                {feedback.severity ?? "—"}
              </Badge>
              <Badge variant="outline" className="border-white/10 text-titanium">
                {BETA_TYPE_LABELS[feedback.type ?? "autre"]}
              </Badge>
            </div>

            <h3 className="text-lg font-medium text-ivory">{feedback.title}</h3>

            <p className="text-xs text-titanium">
              {feedback.tester_name ?? "Testeuse"} · {feedback.project_name} ·{" "}
              {format(new Date(feedback.created_at), "d MMMM yyyy à HH:mm", {
                locale: fr,
              })}
            </p>

            {feedback.description ? (
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-ivory/90">
                {feedback.description}
              </p>
            ) : null}

            {feedback.screenshot_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={feedback.screenshot_url}
                alt="Screenshot"
                className="w-full rounded-lg border border-white/10"
              />
            ) : null}

            {feedback.ticket_id ? (
              <Link
                href={ticketHref(feedback.ticket_id)}
                className="inline-flex items-center gap-2 rounded-lg border border-copper/30 bg-copper/10 px-3 py-2 text-sm text-copper-glow transition hover:bg-copper/15"
              >
                🎟️ Ticket créé
                <ExternalLink className="h-3.5 w-3.5" />
              </Link>
            ) : null}
          </div>
        </ScrollArea>
      </aside>
    </>
  );
}
