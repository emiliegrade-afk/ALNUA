"use client";

import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, Crown, HelpCircle, Loader2, Sparkles, XCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CeoDossierDetailDialog } from "@/components/ceo/ceo-dossier-detail-dialog";
import { CeoSlideCard, CeoSlideRail } from "@/components/ceo/ceo-slide-rail";
import {
  fetchCeoQueue,
  type CeoPendingDossier,
} from "@/lib/rnd-dossier";
import { cn } from "@/lib/utils";

const QUEUE_EXPLAINER =
  "Ici : les idées produit étudiées par le lab R&D. Chaque carte = une idée (app, feature, business). Le comité a bossé dessus ; toi, tu décides si ALNUA lance ou non. Ce n’est pas un fichier Word — c’est une fiche de décision.";

function RecommendationBadge({ value }: { value?: string | null }) {
  if (!value) return null;
  const map: Record<string, { label: string; icon: React.ReactNode; cls: string }> = {
    GO: {
      label: "Avis comité : GO",
      icon: <CheckCircle2 className="h-3 w-3" />,
      cls: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
    },
    MAYBE: {
      label: "Avis : MAYBE",
      icon: <HelpCircle className="h-3 w-3" />,
      cls: "border-amber-500/30 bg-amber-500/10 text-amber-200",
    },
    NO: {
      label: "Avis : NO",
      icon: <XCircle className="h-3 w-3" />,
      cls: "border-red-500/30 bg-red-500/10 text-red-300",
    },
  };
  const cfg = map[value] ?? map.MAYBE;
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold", cfg.cls)}>
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

function domainLabel(domain: string): string {
  const map: Record<string, string> = {
    app: "Produit app",
    gaming: "Gaming",
    robo: "Robotique",
    marketing: "Marketing",
    hardware: "Hardware",
    autre: "Autre",
  };
  return map[domain] ?? domain;
}

function DossierSlide({
  dossier,
  kind,
  onOpen,
}: {
  dossier: CeoPendingDossier;
  kind: "validate" | "prepare";
  onOpen: (d: CeoPendingDossier) => void;
}) {
  const label =
    dossier.waiting_label ?? (kind === "validate" ? "À décider" : "À préparer");
  const why =
    dossier.why_waiting ??
    (kind === "validate"
      ? "Le comité a fini — à toi d’approuver ou de refuser le lancement."
      : "Il manque encore le résumé CEO : génère-le puis décide.");
  const pitch =
    dossier.blurb ||
    dossier.tagline ||
    `Idée R&D dans le domaine « ${domainLabel(dossier.domain)} ».`;

  return (
    <CeoSlideCard onClick={() => onOpen(dossier)}>
      <div className="mb-1.5 flex flex-wrap items-center gap-2">
        <span
          className={cn(
            "rounded border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
            kind === "validate"
              ? "border-emerald-500/35 bg-emerald-500/10 text-emerald-300"
              : "border-amber-500/35 bg-amber-500/10 text-amber-200",
          )}
        >
          {label}
        </span>
        <span className="rounded border border-copper/20 px-1.5 py-0.5 text-[10px] text-copper/90">
          {domainLabel(dossier.domain)}
        </span>
        <RecommendationBadge value={dossier.recommendation} />
      </div>

      <p className="text-sm font-medium leading-snug text-ivory">{dossier.title}</p>
      <p className="mt-1.5 text-[12px] leading-relaxed text-ivory/80">{pitch}</p>
      <p className="mt-2 text-[11px] leading-relaxed text-titanium/65">{why}</p>
      <p className="mt-2 text-[11px] font-medium text-copper">
        Ouvrir → lire le dossier et décider
      </p>
    </CeoSlideCard>
  );
}

export function CeoPendingDossiersCard() {
  const [toValidate, setToValidate] = useState<CeoPendingDossier[]>([]);
  const [toPrepare, setToPrepare] = useState<CeoPendingDossier[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<CeoPendingDossier | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const queue = await fetchCeoQueue();
      setToValidate(queue.to_validate);
      setToPrepare(queue.to_prepare);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de charger les dossiers.");
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
    <>
      <Card className="border-copper/30 bg-transparent shadow-[0_0_24px_rgba(201,149,108,0.06)]">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Crown className="h-4 w-4 text-copper" />
              <CardTitle className="font-title text-base text-ivory">
                Idées R&D à décider
              </CardTitle>
            </div>
            {!loading && total > 0 ? (
              <span className="rounded-full border border-copper/30 bg-copper/10 px-2 py-0.5 text-[10px] font-medium text-copper">
                {total}
              </span>
            ) : null}
          </div>
          <p className="mt-2 rounded-lg border border-copper/20 bg-copper/[0.06] px-3 py-2 text-[12px] leading-relaxed text-ivory/85">
            {QUEUE_EXPLAINER}
          </p>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center gap-2 py-4 text-sm text-titanium/60">
              <Loader2 className="h-4 w-4 animate-spin text-copper/50" />
              Chargement…
            </div>
          ) : error ? (
            <p className="font-body text-sm text-red-400">{error}</p>
          ) : total === 0 ? (
            <p className="font-body text-sm leading-relaxed text-titanium/60">
              Aucune idée en attente. Quand le lab R&D clôture un comité sur une idée,
              elle apparaît ici pour ton OK (ou ton non).
            </p>
          ) : (
            <CeoSlideRail ariaLabel="Idées R&D à décider" maxHeightClass="max-h-[340px]">
              {toValidate.map((d) => (
                <DossierSlide key={d.id} dossier={d} kind="validate" onOpen={setSelected} />
              ))}
              {toPrepare.map((d) => (
                <DossierSlide key={d.id} dossier={d} kind="prepare" onOpen={setSelected} />
              ))}
              {toPrepare.length > 0 ? (
                <div className="flex w-full shrink-0 snap-start items-start gap-2 rounded-xl border border-dashed border-amber-500/25 px-3 py-2 text-[11px] leading-relaxed text-amber-100/85">
                  <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                  <span>
                    {toPrepare.length} idée(s) encore sans résumé CEO — ouvre la carte,
                    génère le package, puis décide.
                  </span>
                </div>
              ) : null}
            </CeoSlideRail>
          )}
        </CardContent>
      </Card>

      <CeoDossierDetailDialog
        dossier={selected}
        open={selected != null}
        onOpenChange={(open) => {
          if (!open) setSelected(null);
        }}
        onChanged={() => void load()}
      />
    </>
  );
}
