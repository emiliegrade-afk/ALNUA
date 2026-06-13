"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AlertCircle,
  FileText,
  FolderOpen,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  fetchRndDossiers,
  type RndDossierListItem,
} from "@/lib/rnd-dossier";
import { cn } from "@/lib/utils";

const STATUS_LABELS: Record<string, string> = {
  draft: "Brouillon",
  committee_active: "Comité actif",
  partial_validated: "Partiellement validé",
  ready_for_ceo: "Prêt CEO",
  ceo_approved: "Approuvé CEO",
  ceo_rejected: "Rejeté",
  in_conception: "En conception",
  published: "Publié",
  archived: "Archivé",
};

function StatusBadge({ status }: { status: string }) {
  const cls =
    status === "ceo_approved"
      ? "border-emerald-500/25 bg-emerald-500/10 text-emerald-400"
      : status === "ceo_rejected"
        ? "border-red-500/25 bg-red-500/10 text-red-400"
        : status === "committee_active"
          ? "border-copper/30 bg-copper/10 text-copper"
          : "border-white/10 bg-white/5 text-titanium/70";
  return (
    <span className={cn("rounded-full border px-2 py-0.5 text-[10px] font-medium", cls)}>
      {STATUS_LABELS[status] ?? status}
    </span>
  );
}

interface RndDossierListProps {
  onSelect?: (dossier: RndDossierListItem) => void;
  selectedId?: string | null;
  /** Increment to force reload (e.g. when tab becomes active). */
  reloadKey?: number;
}

export function RndDossierList({
  onSelect,
  selectedId,
  reloadKey = 0,
}: RndDossierListProps) {
  const [dossiers, setDossiers] = useState<RndDossierListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRndDossiers();
      setDossiers(data);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Impossible de charger les dossiers";
      setError(msg);
      setDossiers([]);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load, reloadKey]);

  if (loading) {
    return (
      <div className="flex h-32 items-center justify-center">
        <Loader2 className="h-5 w-5 animate-spin text-copper/50" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-10 text-center">
        <AlertCircle className="h-10 w-10 text-red-400/70" />
        <p className="max-w-sm text-sm text-red-300/90">{error}</p>
        <p className="max-w-sm text-xs text-titanium/50">
          Vérifie que l&apos;API tourne :{" "}
          <code className="text-copper/80">uvicorn api.main:app --port 8000</code>
        </p>
        <Button size="sm" variant="outline" onClick={load} className="border-white/10">
          <RefreshCw className="mr-2 h-3.5 w-3.5" />
          Réessayer
        </Button>
      </div>
    );
  }

  if (dossiers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-12 text-center">
        <FolderOpen className="h-10 w-10 text-copper/20" />
        <p className="text-sm text-ivory/60">Aucun dossier R&D pour l&apos;instant</p>
        <p className="max-w-sm text-xs text-titanium/50">
          Promouvez une idée depuis le Centre R&D — le dossier sera enrichi
          (sections + business case).
        </p>
        <Button size="sm" variant="outline" onClick={load} className="border-white/10">
          <RefreshCw className="mr-2 h-3.5 w-3.5" />
          Actualiser
        </Button>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col gap-2">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs text-titanium/50">
          {dossiers.length} dossier{dossiers.length > 1 ? "s" : ""}
        </p>
        <Button
          size="sm"
          variant="outline"
          onClick={load}
          className="border-white/10 text-titanium/70"
        >
          <RefreshCw className="h-3.5 w-3.5" />
        </Button>
      </div>
      <div className="min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
        {dossiers.map((d) => (
          <button
            key={d.id}
            type="button"
            onClick={() => onSelect?.(d)}
            className={cn(
              "w-full rounded-xl border p-4 text-left transition",
              selectedId === d.id
                ? "border-copper/40 bg-copper/10"
                : "border-copper/10 bg-white/[0.02] hover:border-copper/25 hover:bg-white/[0.04]"
            )}
          >
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <StatusBadge status={d.status} />
              <span className="rounded-full border border-white/10 px-2 py-0.5 text-[10px] text-titanium/60">
                {d.domain}
              </span>
            </div>
            <p className="text-sm font-medium text-ivory/90">{d.title}</p>
            <p className="mt-1 text-[11px] text-titanium/50">
              {d.sections_validated_count}/{d.sections_total_count} sections · {d.slug}
            </p>
          </button>
        ))}
      </div>
    </div>
  );
}
