"use client";

import { format } from "date-fns";
import { fr } from "date-fns/locale";
import { Trash2, X } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  WAITLIST_SOURCE_LABELS,
  WAITLIST_STATUSES,
  WAITLIST_STATUS_LABELS,
  sourceBadgeStyle,
  statusBadgeStyle,
} from "@/components/waitlist/waitlist.constants";
import {
  deleteWaitlistEntry,
  updateWaitlistStatus,
  type WaitlistEntry,
  type WaitlistStatus,
} from "@/lib/waitlist-api";
import { cn } from "@/lib/utils";

interface WaitlistDetailPanelProps {
  entry: WaitlistEntry | null;
  open: boolean;
  onClose: () => void;
  onUpdated: () => void;
}

export function WaitlistDetailPanel({
  entry,
  open,
  onClose,
  onUpdated,
}: WaitlistDetailPanelProps) {
  if (!open || !entry) return null;

  const handleStatusChange = async (status: WaitlistStatus) => {
    try {
      await updateWaitlistStatus(entry.id, status);
      toast.success("Statut mis à jour");
      onUpdated();
      onClose();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    }
  };

  const handleDelete = async () => {
    if (!confirm("Supprimer cette inscription ?")) return;
    try {
      await deleteWaitlistEntry(entry.id);
      toast.success("Inscription supprimée");
      onUpdated();
      onClose();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    }
  };

  return (
    <>
      <button
        type="button"
        aria-label="Fermer"
        className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      <aside
        className={cn(
          "fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col border-l border-copper/15 bg-surface shadow-2xl",
          "animate-fade-in"
        )}
      >
        <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
          <h2 className="text-sm font-semibold text-ivory">Détail inscription</h2>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Fermer">
            <X className="h-4 w-4" />
          </Button>
        </div>

        <ScrollArea className="flex-1 px-5 py-4">
          <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline" className={statusBadgeStyle(entry.status)}>
                {WAITLIST_STATUS_LABELS[entry.status] ?? entry.status}
              </Badge>
              <Badge
                variant="outline"
                className={sourceBadgeStyle(entry.source)}
              >
                {WAITLIST_SOURCE_LABELS[entry.source ?? "direct"] ?? entry.source}
              </Badge>
            </div>

            <div>
              <p className="text-lg font-medium text-ivory">
                {entry.first_name ?? "—"}
              </p>
              <p className="text-sm text-titanium">{entry.email}</p>
            </div>

            <p className="text-xs text-titanium">
              {entry.project_name} ·{" "}
              {format(new Date(entry.created_at), "d MMMM yyyy à HH:mm", {
                locale: fr,
              })}
            </p>

            {entry.message ? (
              <div className="rounded-lg border border-white/10 bg-white/[0.02] p-4">
                <p className="mb-2 text-xs font-medium uppercase tracking-wide text-titanium">
                  Pourquoi elle veut essayer
                </p>
                <p className="whitespace-pre-wrap text-sm leading-relaxed text-ivory/90">
                  {entry.message}
                </p>
              </div>
            ) : (
              <p className="text-sm italic text-titanium/60">
                Aucun message laissé
              </p>
            )}

            <div>
              <p className="mb-2 text-xs text-titanium">Changer le statut</p>
              <Select
                value={entry.status}
                onValueChange={(v) => handleStatusChange(v as WaitlistStatus)}
              >
                <SelectTrigger className="border-white/10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {WAITLIST_STATUSES.map((s) => (
                    <SelectItem key={s.id} value={s.id}>
                      {s.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </ScrollArea>

        <div className="border-t border-white/10 p-4">
          <Button
            variant="outline"
            className="w-full gap-2 border-red-500/30 text-red-300 hover:bg-red-500/10"
            onClick={handleDelete}
          >
            <Trash2 className="h-4 w-4" />
            Supprimer
          </Button>
        </div>
      </aside>
    </>
  );
}
