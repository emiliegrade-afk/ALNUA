"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Loader2, RefreshCw, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  fetchTodayBriefing,
  type DailyBriefing,
} from "@/lib/briefing-api";
import { ROUTES } from "@/lib/routes";
import { C } from "@/app/app-v2/shared";

/** Compact morning strip for /ceo — cached brief, no second LLM by default. */
export function CeoMorningBriefCard() {
  const [briefing, setBriefing] = useState<DailyBriefing | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const data = await fetchTodayBriefing({ ensure: false, timeoutMs: 8_000 });
      setBriefing(data);
    } catch {
      setBriefing(null);
      setError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div
      className="rounded-xl border px-4 py-3"
      style={{ borderColor: C.copperLine, background: "transparent" }}
    >
      <div className="mb-2 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Sun className="h-4 w-4" style={{ color: C.copper }} />
          <p className="text-sm font-medium" style={{ color: C.ivory }}>
            Brief du jour
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            type="button"
            size="sm"
            variant="ghost"
            className="h-7 px-2 text-titanium"
            onClick={() => void load()}
            disabled={loading}
            aria-label="Rafraîchir le brief"
          >
            {loading ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <RefreshCw className="h-3.5 w-3.5" />
            )}
          </Button>
          <Link
            href={ROUTES.briefing}
            className="text-[11px] text-copper hover:text-copper-light"
          >
            Voir tout →
          </Link>
        </div>
      </div>
      {loading && !briefing ? (
        <p className="text-[11px]" style={{ color: C.dim }}>
          Chargement…
        </p>
      ) : error && !briefing ? (
        <p className="text-[11px]" style={{ color: C.dim }}>
          Brief indisponible — ouvre{" "}
          <Link href={ROUTES.briefing} className="text-copper">
            /briefing
          </Link>{" "}
          ou demande à Nadia « priorités du jour ».
        </p>
      ) : (
        <div className="space-y-1.5">
          <p className="text-sm leading-snug" style={{ color: C.ivory }}>
            {briefing?.summary?.trim() || "Pas encore de résumé pour aujourd’hui."}
          </p>
          {briefing?.has_urgent ? (
            <p className="text-[11px] text-amber-200/90">
              ⚠ {briefing.urgent_count} alerte
              {briefing.urgent_count > 1 ? "s" : ""} — à traiter
            </p>
          ) : null}
          <p className="text-[11px]" style={{ color: C.dim }}>
            Mails & planning →{" "}
            <Link href={ROUTES.secretary} className="text-copper hover:text-copper-light">
              bureau Nadia
            </Link>
          </p>
        </div>
      )}
    </div>
  );
}
