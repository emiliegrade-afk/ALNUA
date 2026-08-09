"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { CheckCircle2, Crown, HelpCircle, Loader2, Sparkles, XCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ceoDossierHref,
  fetchCeoQueue,
  type CeoPendingDossier,
} from "@/lib/rnd-dossier";
import { cn } from "@/lib/utils";

function RecommendationBadge({ value }: { value?: string | null }) {
  if (!value) return null;
  const map: Record<string, { label: string; icon: React.ReactNode; cls: string }> = {
    GO: {
      label: "GO",
      icon: <CheckCircle2 className="h-3 w-3" />,
      cls: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
    },
    MAYBE: {
      label: "MAYBE",
      icon: <HelpCircle className="h-3 w-3" />,
      cls: "border-amber-500/30 bg-amber-500/10 text-amber-200",
    },
    NO: {
      label: "NO",
      icon: <XCircle className="h-3 w-3" />,
      cls: "border-red-500/30 bg-red-500/10 text-red-300",
    },
  };
  const cfg = map[value] ?? map.MAYBE;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold",
        cfg.cls
      )}
    >
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

function DossierRow({
  dossier,
  actionLabel,
}: {
  dossier: CeoPendingDossier;
  actionLabel: string;
}) {
  return (
    <li>
      <Link
        href={ceoDossierHref(dossier, "ceo")}
        className="group flex flex-col gap-1.5 rounded-lg border border-copper/15 bg-obsidian-deep/40 px-3 py-2.5 transition hover:border-copper/35 hover:bg-copper/[0.04]"
      >
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="font-body text-sm font-medium text-ivory/90 group-hover:text-ivory">
            {dossier.title}
          </span>
          <RecommendationBadge value={dossier.recommendation} />
        </div>
        <div className="flex flex-wrap items-center gap-2 text-[10px] text-titanium/55">
          <span className="rounded border border-copper/15 px-1.5 py-0.5">
            {dossier.domain}
          </span>
          {dossier.slug ? (
            <span className="rounded border border-copper/15 px-1.5 py-0.5">
              {dossier.slug}
            </span>
          ) : null}
          <span className="text-copper/80">{actionLabel}</span>
        </div>
      </Link>
    </li>
  );
}

export function CeoPendingDossiersCard() {
  const [toValidate, setToValidate] = useState<CeoPendingDossier[]>([]);
  const [toPrepare, setToPrepare] = useState<CeoPendingDossier[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const queue = await fetchCeoQueue();
      setToValidate(queue.to_validate);
      setToPrepare(queue.to_prepare);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Impossible de charger les dossiers."
      );
      setToValidate([]);
      setToPrepare([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const total = toValidate.length + toPrepare.length;

  return (
    <Card className="border-copper/30 bg-obsidian-2/90 shadow-[0_0_24px_rgba(201,149,108,0.06)]">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Crown className="h-4 w-4 text-copper" />
            <CardTitle className="font-title text-base text-ivory">
              Dossiers R&D — Bureau CEO
            </CardTitle>
          </div>
          {!loading && total > 0 ? (
            <span className="rounded-full border border-copper/30 bg-copper/10 px-2 py-0.5 text-[10px] font-medium text-copper">
              {total}
            </span>
          ) : null}
        </div>
        <p className="font-body text-xs text-titanium/60">
          À valider (package prêt) ou à finaliser (générer le dossier CEO)
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {loading ? (
          <div className="flex items-center gap-2 py-4 text-sm text-titanium/60">
            <Loader2 className="h-4 w-4 animate-spin text-copper/50" />
            Chargement des dossiers…
          </div>
        ) : error ? (
          <p className="font-body text-sm text-red-400">{error}</p>
        ) : total === 0 ? (
          <p className="font-body text-sm text-titanium/60">
            Aucun dossier en attente. Clôture un comité R&D pour alimenter la file.
          </p>
        ) : (
          <>
            {toValidate.length > 0 ? (
              <div>
                <p className="mb-2 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wider text-emerald-300/80">
                  <CheckCircle2 className="h-3 w-3" />
                  À valider ({toValidate.length})
                </p>
                <ul className="space-y-2">
                  {toValidate.map((d) => (
                    <DossierRow key={d.id} dossier={d} actionLabel="Approuver →" />
                  ))}
                </ul>
              </div>
            ) : null}

            {toPrepare.length > 0 ? (
              <div>
                <p className="mb-2 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wider text-amber-200/80">
                  <Sparkles className="h-3 w-3" />
                  À finaliser ({toPrepare.length})
                </p>
                <ul className="space-y-2">
                  {toPrepare.map((d) => (
                    <DossierRow
                      key={d.id}
                      dossier={d}
                      actionLabel="Générer dossier CEO →"
                    />
                  ))}
                </ul>
              </div>
            ) : null}
          </>
        )}
      </CardContent>
    </Card>
  );
}
