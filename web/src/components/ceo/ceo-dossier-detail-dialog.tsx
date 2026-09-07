"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  ExternalLink,
  HelpCircle,
  Loader2,
  Sparkles,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  ceoDossierHref,
  decideCeoPackage,
  fetchCeoPackage,
  fetchRndDossier,
  generateCeoPackage,
  type CeoPackageResponse,
  type CeoPendingDossier,
  type RndDossierDetail,
} from "@/lib/rnd-dossier";
import { cn } from "@/lib/utils";

const DOSSIER_EXPLAINER =
  "C’est une idée produit étudiée par le lab R&D (pas un fichier admin). Le comité a déjà analysé problème, solution et finance. Toi : tu décides si ALNUA lance ou non.";

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

function RecoBadge({ value }: { value?: string | null }) {
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
    <span className={cn("inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold", cfg.cls)}>
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

type Props = {
  dossier: CeoPendingDossier | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onChanged: () => void;
};

/** Modal CEO — ouvre le dossier, explique, actions decide / generate. */
export function CeoDossierDetailDialog({
  dossier,
  open,
  onOpenChange,
  onChanged,
}: Props) {
  const [detail, setDetail] = useState<RndDossierDetail | null>(null);
  const [pack, setPack] = useState<CeoPackageResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!dossier) return;
    setLoading(true);
    setError(null);
    setDetail(null);
    setPack(null);
    const ref = dossier.id || dossier.slug;
    try {
      const d = await fetchRndDossier(ref);
      setDetail(d);
      try {
        setPack(await fetchCeoPackage(d.id));
      } catch {
        setPack(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Dossier introuvable");
    } finally {
      setLoading(false);
    }
  }, [dossier]);

  useEffect(() => {
    if (open && dossier) void load();
  }, [open, dossier, load]);

  async function run(key: string, fn: () => Promise<void>) {
    if (!detail) return;
    setBusy(key);
    try {
      await fn();
      onChanged();
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Action échouée");
    } finally {
      setBusy(null);
    }
  }

  const title = detail?.title ?? dossier?.title ?? "Dossier";
  const reco =
    dossier?.recommendation ??
    (typeof pack?.package?.recommendation === "string"
      ? pack.package.recommendation
      : null);
  const markdown = pack?.markdown ?? detail?.one_pager_md ?? detail?.committee_report_md;
  const workspaceHref = dossier
    ? ceoDossierHref({ id: detail?.id ?? dossier.id, slug: detail?.slug ?? dossier.slug }, "ceo")
    : "/rd";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[min(90vh,720px)] w-[min(640px,94vw)] flex-col gap-0 overflow-hidden border-copper/25 bg-obsidian p-0 sm:max-w-xl">
        <DialogHeader className="shrink-0 space-y-2 border-b border-copper/15 px-5 py-4 text-left">
          <DialogTitle className="pr-8 text-lg text-ivory">{title}</DialogTitle>
          <DialogDescription className="text-[12px] leading-relaxed text-titanium/70">
            {DOSSIER_EXPLAINER}
          </DialogDescription>
          {dossier?.why_waiting ? (
            <p className="rounded-lg border border-copper/20 bg-copper/[0.07] px-3 py-2 text-[12px] leading-relaxed text-ivory/85">
              <span className="font-medium text-copper">Pourquoi c’est ici : </span>
              {dossier.why_waiting}
            </p>
          ) : null}
        </DialogHeader>

        <div className="alnua-scroll min-h-0 flex-1 space-y-4 overflow-y-auto px-5 py-4">
          {loading ? (
            <p className="flex items-center gap-2 text-sm text-titanium/60">
              <Loader2 className="h-4 w-4 animate-spin text-copper" />
              Chargement de l’idée…
            </p>
          ) : error ? (
            <p className="text-sm text-danger">{error}</p>
          ) : (
            <>
              <div className="flex flex-wrap items-center gap-2 text-[11px]">
                <span className="rounded border border-copper/25 px-1.5 py-0.5 text-copper">
                  {domainLabel(detail?.domain ?? dossier?.domain ?? "")}
                </span>
                <span className="rounded border border-titanium/20 px-1.5 py-0.5 text-titanium/70">
                  {dossier?.waiting_label ?? "En file CEO"}
                </span>
                <RecoBadge value={reco} />
                {detail ? (
                  <span className="text-titanium/50">
                    {detail.sections_validated_count}/{detail.sections_total_count} parties validées par le comité
                  </span>
                ) : null}
              </div>

              {(detail?.tagline || dossier?.blurb) ? (
                <div>
                  <p className="mb-1 text-[10px] uppercase tracking-wider text-titanium/50">
                    En une phrase
                  </p>
                  <p className="text-sm leading-relaxed text-ivory">
                    {detail?.tagline || dossier?.blurb}
                  </p>
                </div>
              ) : null}

              {detail?.vision_snapshot ? (
                <div>
                  <p className="mb-1 text-[10px] uppercase tracking-wider text-titanium/50">
                    De quoi ça parle
                  </p>
                  <p className="whitespace-pre-wrap text-[12px] leading-relaxed text-titanium/85">
                    {detail.vision_snapshot}
                  </p>
                </div>
              ) : null}

              {markdown ? (
                <div>
                  <p className="mb-1 text-[10px] uppercase tracking-wider text-titanium/50">
                    Résumé CEO (package)
                  </p>
                  <pre className="max-h-52 overflow-auto whitespace-pre-wrap rounded-lg border border-copper/15 bg-obsidian-deep/70 p-3 text-[11px] leading-relaxed text-titanium/85">
                    {markdown.slice(0, 4000)}
                    {markdown.length > 4000 ? "…" : ""}
                  </pre>
                </div>
              ) : (
                <p className="rounded-lg border border-amber-500/25 bg-amber-500/5 px-3 py-2 text-[12px] leading-relaxed text-amber-100/90">
                  Pas encore de résumé CEO pour cette idée. Clique « Générer le résumé »
                  pour qu’Aria / Noé te préparent la fiche, puis tu pourras approuver ou refuser.
                </p>
              )}
            </>
          )}
        </div>

        <div className="flex shrink-0 flex-wrap gap-2 border-t border-copper/15 px-5 py-3">
          <Button asChild size="sm" variant="outline" className="border-copper/35 text-copper">
            <Link href={workspaceHref} target="_blank" rel="noreferrer">
              <ExternalLink className="mr-1 h-3.5 w-3.5" />
              Voir tout le dossier R&D
            </Link>
          </Button>
          {(dossier?.needs_action === "generate_package" || pack?.can_generate) && detail ? (
            <Button
              size="sm"
              variant="outline"
              className="border-amber-500/35 text-amber-200"
              disabled={busy != null}
              onClick={() =>
                void run("gen", async () => {
                  await generateCeoPackage(detail.id);
                  toast.success("Résumé CEO généré");
                })
              }
            >
              {busy === "gen" ? <Loader2 className="mr-1 h-3 w-3 animate-spin" /> : <Sparkles className="mr-1 h-3 w-3" />}
              Générer le résumé
            </Button>
          ) : null}
          {(dossier?.can_decide || pack?.can_decide) && detail ? (
            <>
              <Button
                size="sm"
                className="bg-emerald-600/90 text-ivory hover:bg-emerald-500"
                disabled={busy != null}
                onClick={() =>
                  void run("ok", async () => {
                    await decideCeoPackage(detail.id, { ceo_status: "approved" });
                    toast.success("Idée approuvée — ALNUA peut lancer");
                    onOpenChange(false);
                  })
                }
              >
                {busy === "ok" ? <Loader2 className="mr-1 h-3 w-3 animate-spin" /> : <CheckCircle2 className="mr-1 h-3 w-3" />}
                Oui, on lance
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="border-danger/40 text-danger"
                disabled={busy != null}
                onClick={() =>
                  void run("no", async () => {
                    await decideCeoPackage(detail.id, { ceo_status: "rejected" });
                    toast.success("Idée refusée");
                    onOpenChange(false);
                  })
                }
              >
                {busy === "no" ? <Loader2 className="mr-1 h-3 w-3 animate-spin" /> : <XCircle className="mr-1 h-3 w-3" />}
                Non, on ne lance pas
              </Button>
            </>
          ) : null}
        </div>
      </DialogContent>
    </Dialog>
  );
}
