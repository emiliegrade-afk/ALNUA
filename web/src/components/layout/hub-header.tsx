"use client";

import { format } from "date-fns";
import { fr } from "date-fns/locale";
import { RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

interface HubHeaderProps {
  apiOnline: boolean | null;
  apiAuthenticated?: boolean | null;
  onRefresh?: () => void;
  refreshing?: boolean;
}

export function HubHeader({
  apiOnline,
  apiAuthenticated = null,
  onRefresh,
  refreshing,
}: HubHeaderProps) {
  const now = new Date();
  const statusLabel =
    apiOnline === null
      ? "…"
      : !apiOnline
        ? "offline"
        : apiAuthenticated === false
          ? "clé API invalide"
          : "connectée";
  const isChecking = apiOnline === null;

  return (
    <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="forge-heading text-[11px] text-copper/80">
          {format(now, "EEEE d MMMM yyyy", { locale: fr })}
        </p>
        <h1 className="mt-1 text-2xl font-semibold tracking-wide text-ivory">
          Mission Control
        </h1>
        <p className="mt-1 text-sm text-titanium">
          Cockpit opérationnel — parle au COO, surveille tes projets.
        </p>
      </div>

      <div className="flex items-center gap-3">
        <div
          className={cn(
            "flex items-center gap-2 rounded-full px-3 py-1.5 text-xs ring-1",
            isChecking
              ? "bg-white/[0.04] text-titanium/80 ring-white/[0.08]"
              : !apiOnline
                ? "bg-red-500/10 text-red-400 ring-red-500/20"
                : apiAuthenticated === false
                  ? "bg-amber-500/10 text-amber-400 ring-amber-500/20"
                  : "bg-emerald-500/10 text-emerald-400 ring-emerald-500/20"
          )}
        >
          <span
            className={cn(
              "status-dot",
              isChecking
                ? "animate-pulse bg-titanium/50"
                : !apiOnline
                  ? "bg-red-500"
                  : apiAuthenticated === false
                    ? "bg-amber-500"
                    : "status-dot-active"
            )}
          />
          API {statusLabel}
        </div>

        {onRefresh && (
          <button
            type="button"
            onClick={onRefresh}
            disabled={refreshing}
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/[0.08] bg-white/[0.03] text-titanium/80 transition hover:bg-copper/10 hover:text-ivory disabled:opacity-50"
            aria-label="Actualiser"
          >
            <RefreshCw
              className={cn("h-4 w-4", refreshing && "animate-spin")}
            />
          </button>
        )}
      </div>
    </header>
  );
}
