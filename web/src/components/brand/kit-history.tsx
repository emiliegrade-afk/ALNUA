"use client";

import { formatDistanceToNow } from "date-fns";
import { fr } from "date-fns/locale";
import { History } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { BrandKitSummary } from "@/lib/brand-api";
import { ALL_FORMAT_NAMES } from "@/lib/brand-api";

interface KitHistoryProps {
  kits: BrandKitSummary[];
  activeKitId: string | null;
  onSelect: (kitId: string) => void;
  loading?: boolean;
}

export function KitHistory({
  kits,
  activeKitId,
  onSelect,
  loading = false,
}: KitHistoryProps) {
  if (loading) {
    return (
      <p className="text-sm text-titanium/60">Chargement de l&apos;historique…</p>
    );
  }

  if (kits.length === 0) {
    return (
      <p className="text-sm text-titanium/60">
        Aucun kit enregistré pour ce projet.
      </p>
    );
  }

  return (
    <ul className="space-y-2">
      {kits.map((kit) => {
        const isActive = kit.id === activeKitId;
        const formatCount = kit.formats_generated.length;
        const isComplete =
          kit.is_complete || formatCount >= ALL_FORMAT_NAMES.length;

        let dateLabel = "";
        if (kit.created_at) {
          try {
            dateLabel = formatDistanceToNow(new Date(kit.created_at), {
              addSuffix: true,
              locale: fr,
            });
          } catch {
            dateLabel = "";
          }
        }

        return (
          <li key={kit.id}>
            <Button
              type="button"
              variant="ghost"
              onClick={() => onSelect(kit.id)}
              className={`h-auto w-full justify-start gap-3 rounded-xl border px-3 py-3 text-left ${
                isActive
                  ? "border-copper/40 bg-copper/10"
                  : "border-copper/10 bg-black/20 hover:bg-copper/5"
              }`}
            >
              <History className="mt-0.5 h-4 w-4 shrink-0 text-copper/70" />
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium text-ivory">{kit.brand_name}</p>
                <p className="text-[11px] text-titanium/70">
                  {formatCount} format{formatCount !== 1 ? "s" : ""}
                  {dateLabel ? ` · ${dateLabel}` : ""}
                </p>
              </div>
              {isComplete ? (
                <Badge className="shrink-0 bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/20">
                  20 formats
                </Badge>
              ) : (
                <Badge variant="outline" className="shrink-0 text-titanium">
                  {formatCount}/{ALL_FORMAT_NAMES.length}
                </Badge>
              )}
            </Button>
          </li>
        );
      })}
    </ul>
  );
}
