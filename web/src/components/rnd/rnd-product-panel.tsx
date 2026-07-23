"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  ExternalLink,
  Globe,
  Loader2,
  Lock,
  Rocket,
  ToggleLeft,
  ToggleRight,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { MarkdownContent } from "@/components/shared/markdown-content";
import {
  fetchProductStatus,
  generateProductPage,
  publishProductPage,
  unpublishProductPage,
  type RndProductPage,
  type DossierStatus,
} from "@/lib/rnd-dossier";
import { hubPublicApiUrl } from "@/lib/hub-api-config";

export interface RndProductPanelProps {
  dossierId: string;
  dossierTitle: string;
  dossierStatus: DossierStatus;
  ceoStatus?: string | null;
  onUpdated?: () => void;
}

export function RndProductPanel({
  dossierId,
  dossierTitle,
  onUpdated,
}: RndProductPanelProps) {
  const [status, setStatus] = useState<Awaited<
    ReturnType<typeof fetchProductStatus>
  > | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [publishing, setPublishing] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setStatus(await fetchProductStatus(dossierId));
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur chargement fiche produit");
      setStatus(null);
    } finally {
      setLoading(false);
    }
  }, [dossierId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleGenerate(force = false) {
    setGenerating(true);
    try {
      const r = await generateProductPage(dossierId, {
        force,
        waitlistEnabled: status?.page?.waitlist_enabled ?? true,
      });
      toast.success(r.message);
      await load();
      onUpdated?.();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Génération impossible");
    } finally {
      setGenerating(false);
    }
  }

  async function handlePublish() {
    setPublishing(true);
    try {
      const r = await publishProductPage(dossierId);
      toast.success(r.message);
      await load();
      onUpdated?.();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Publication impossible");
    } finally {
      setPublishing(false);
    }
  }

  async function handleUnpublish() {
    setPublishing(true);
    try {
      const r = await unpublishProductPage(dossierId);
      toast.success(r.message);
      await load();
      onUpdated?.();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Dépublication impossible");
    } finally {
      setPublishing(false);
    }
  }

  if (loading) {
    return (
      <div className="flex h-48 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-copper/50" />
      </div>
    );
  }

  const page = status?.page;
  const locked = !status?.unlocked;

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-6">
      <div>
        <div className="mb-2 flex items-center gap-2">
          <Globe className="h-5 w-5 text-copper" />
          <h2 className="font-title text-xl text-ivory">Fiche produit publique</h2>
        </div>
        <p className="text-sm leading-relaxed text-titanium/70">
          Landing page publique pour{" "}
          <span className="text-ivory/90">{dossierTitle}</span> — générée depuis
          le dossier R&D, avec waitlist optionnelle. Publication explicite requise.
        </p>
      </div>

      {locked ? (
        <div className="flex items-start gap-3 rounded-xl border border-amber-500/25 bg-amber-500/10 p-4">
          <Lock className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" />
          <div>
            <p className="text-sm font-medium text-amber-100">Verrouillé — validation CEO requise</p>
            <p className="mt-1 text-xs text-titanium/70">{status?.message}</p>
          </div>
        </div>
      ) : null}

      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          disabled={locked || generating}
          onClick={() => void handleGenerate(Boolean(page))}
          className="bg-copper text-obsidian hover:bg-copper/90"
        >
          {generating ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Rocket className="mr-2 h-4 w-4" />
          )}
          {page ? "Regénérer la fiche" : "Générer la fiche"}
        </Button>
        {page && !page.published ? (
          <Button
            type="button"
            variant="outline"
            disabled={locked || publishing}
            onClick={() => void handlePublish()}
            className="border-emerald-500/35 text-emerald-300 hover:bg-emerald-500/10"
          >
            {publishing ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Globe className="mr-2 h-4 w-4" />
            )}
            Publier
          </Button>
        ) : null}
        {page?.published ? (
          <>
            <Button
              type="button"
              variant="outline"
              disabled={publishing}
              onClick={() => void handleUnpublish()}
              className="border-white/10 text-titanium/80"
            >
              Retirer du site
            </Button>
            {page.public_url ? (
              <Button type="button" variant="outline" asChild className="border-copper/35 text-copper">
                <Link href={`/p/${page.slug}`} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="mr-2 h-4 w-4" />
                  Voir la page live
                </Link>
              </Button>
            ) : null}
          </>
        ) : null}
      </div>

      {page ? (
        <ProductPreview page={page} />
      ) : (
        <div className="rounded-xl border border-dashed border-copper/20 p-8 text-center text-sm text-titanium/60">
          Aucune fiche générée. Valide le dossier CEO puis génère la landing.
        </div>
      )}
    </div>
  );
}

function ProductPreview({ page }: { page: RndProductPage }) {
  return (
    <article className="overflow-hidden rounded-xl border border-copper/15 bg-white/[0.02]">
      <div className="border-b border-copper/10 px-4 py-3">
        <div className="flex flex-wrap items-center gap-2">
          <span
            className={
              page.published
                ? "rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] text-emerald-300"
                : "rounded-full bg-white/10 px-2 py-0.5 text-[10px] text-titanium/60"
            }
          >
            {page.published ? "Publiée" : "Brouillon"}
          </span>
          {page.waitlist_enabled ? (
            <span className="inline-flex items-center gap-1 text-[10px] text-copper">
              <ToggleRight className="h-3 w-3" />
              Waitlist activée
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-[10px] text-titanium/50">
              <ToggleLeft className="h-3 w-3" />
              Sans waitlist
            </span>
          )}
          {page.pricing_model ? (
            <span className="text-[10px] text-titanium/60">{page.pricing_model}</span>
          ) : null}
        </div>
        <h3 className="mt-2 font-title text-lg text-ivory">{page.title}</h3>
        {page.tagline ? (
          <p className="mt-1 text-sm text-titanium/75">{page.tagline}</p>
        ) : null}
      </div>

      {page.hero_url ? (
        <div className="border-b border-copper/10 bg-obsidian/40 p-2">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={
              page.hero_url.startsWith("http")
                ? page.hero_url
                : hubPublicApiUrl(page.hero_url)
            }
            alt=""
            className="mx-auto max-h-48 w-full object-contain"
          />
        </div>
      ) : null}

      <div className="space-y-4 p-4">
        {page.description_html ? (
          <div
            className="prose prose-invert max-w-none prose-p:text-sm prose-p:text-titanium/80 prose-headings:text-ivory prose-headings:text-base"
            dangerouslySetInnerHTML={{ __html: page.description_html }}
          />
        ) : null}

        {page.features.length > 0 ? (
          <div>
            <p className="label-caps mb-2 text-titanium/50">Features</p>
            <ul className="space-y-2">
              {page.features.map((f) => (
                <li key={f.title} className="rounded-lg border border-white/8 bg-white/[0.02] p-3">
                  <p className="text-sm font-medium text-ivory/90">{f.title}</p>
                  <p className="mt-1 text-xs text-titanium/65">{f.description}</p>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {page.faq.length > 0 ? (
          <div>
            <p className="label-caps mb-2 text-titanium/50">FAQ</p>
            <div className="space-y-2">
              {page.faq.map((item) => (
                <div key={item.question} className="rounded-lg border border-white/8 p-3">
                  <p className="text-xs font-medium text-ivory/85">{item.question}</p>
                  <MarkdownContent className="mt-1 text-xs text-titanium/65">
                    {item.answer}
                  </MarkdownContent>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </article>
  );
}
