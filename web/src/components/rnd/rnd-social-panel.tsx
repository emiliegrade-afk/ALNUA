"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  Calendar,
  CheckCircle2,
  Circle,
  Loader2,
  Lock,
  Megaphone,
  Sparkles,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  CONTENT_TYPE_LABELS,
  PLATFORM_STYLES,
  type PostPlatform,
} from "@/components/content/content.constants";
import {
  fetchSocialCalendar,
  fetchSocialStatus,
  generateAllSocialPosts,
  generateSocialCalendar,
  generateSocialPost,
  type DossierStatus,
  type RndSocialCalendarItem,
  type SocialPhase,
} from "@/lib/rnd-dossier";
import { cn } from "@/lib/utils";

const PHASE_LABELS: Record<SocialPhase, string> = {
  internal: "Interne",
  behind_scenes: "Coulisses",
  teaser: "Teaser",
  pre_launch: "Pre-launch",
  launch: "Launch",
  post_launch: "Post-launch",
};

const PHASE_COLORS: Record<SocialPhase, string> = {
  internal: "border-titanium/30 bg-titanium/5",
  behind_scenes: "border-violet-500/25 bg-violet-500/10",
  teaser: "border-amber-500/25 bg-amber-500/10",
  pre_launch: "border-copper/30 bg-copper/10",
  launch: "border-emerald-500/30 bg-emerald-500/10",
  post_launch: "border-sky-500/25 bg-sky-500/10",
};

function formatDate(iso?: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString("fr-FR", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  } catch {
    return iso.slice(0, 10);
  }
}

function StatusIcon({ status }: { status: string }) {
  if (status === "generated" || status === "approved" || status === "published") {
    return <CheckCircle2 className="h-4 w-4 text-emerald-400" />;
  }
  return <Circle className="h-4 w-4 text-titanium/40" />;
}

export interface RndSocialPanelProps {
  dossierId: string;
  dossierTitle: string;
  dossierStatus: DossierStatus;
  ceoStatus?: string | null;
  onUpdated?: () => void;
}

export function RndSocialPanel({
  dossierId,
  dossierTitle,
  dossierStatus,
  ceoStatus,
  onUpdated,
}: RndSocialPanelProps) {
  const [items, setItems] = useState<RndSocialCalendarItem[]>([]);
  const [unlocked, setUnlocked] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [generatingCal, setGeneratingCal] = useState(false);
  const [generatingAll, setGeneratingAll] = useState(false);
  const [generatingItem, setGeneratingItem] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [cal, st] = await Promise.all([
        fetchSocialCalendar(dossierId),
        fetchSocialStatus(dossierId),
      ]);
      setItems(cal);
      setUnlocked(st.unlocked);
      setStatusMessage(st.message);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur chargement calendrier");
      setItems([]);
      setUnlocked(false);
    } finally {
      setLoading(false);
    }
  }, [dossierId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleGenerateCalendar(force = false) {
    setGeneratingCal(true);
    try {
      const r = await generateSocialCalendar(dossierId, { force });
      toast.success(r.message);
      await load();
      onUpdated?.();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur génération calendrier");
    } finally {
      setGeneratingCal(false);
    }
  }

  async function handleGenerateAll() {
    setGeneratingAll(true);
    try {
      const r = await generateAllSocialPosts(dossierId);
      toast.success(r.message);
      await load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur génération posts");
    } finally {
      setGeneratingAll(false);
    }
  }

  async function handleGenerateItem(itemId: string) {
    setGeneratingItem(itemId);
    try {
      const r = await generateSocialPost(dossierId, itemId);
      toast.success(r.message);
      await load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur génération post");
    } finally {
      setGeneratingItem(null);
    }
  }

  const withPosts = items.filter((i) => i.post_id || i.post).length;

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 pb-4">
      <div>
        <div className="mb-2 flex items-center gap-2">
          <Megaphone className="h-5 w-5 text-copper" />
          <h2 className="font-title text-xl text-ivory">Pipeline social</h2>
        </div>
        <p className="text-sm leading-relaxed text-titanium/70">
          Teasers produit pour{" "}
          <span className="text-ivory/90">{dossierTitle}</span> — débloqué après{" "}
          <strong className="font-normal text-ivory/85">validation CEO</strong>, pas pendant
          la phase R&D (comité, dossier en cours). Validation finale dans{" "}
          <Link href="/content" className="text-copper hover:underline">
            Content
          </Link>
          .
        </p>
      </div>

      {!unlocked ? (
        <div className="rounded-xl border border-amber-500/25 bg-amber-500/[0.08] p-4">
          <div className="mb-2 flex items-center gap-2 text-amber-200/90">
            <Lock className="h-4 w-4 shrink-0" />
            <p className="text-sm font-medium">Pipeline social verrouillé</p>
          </div>
          <p className="text-xs leading-relaxed text-titanium/70">
            {statusMessage || "Disponible après validation CEO du dossier."}
            <br />
            Statut actuel : <span className="text-ivory/80">{dossierStatus}</span>
            {ceoStatus ? (
              <>
                {" "}
                · CEO : <span className="text-ivory/80">{ceoStatus}</span>
              </>
            ) : null}
          </p>
        </div>
      ) : null}

      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          onClick={() => handleGenerateCalendar(items.length > 0)}
          disabled={!unlocked || generatingCal || generatingAll}
          className="bg-copper text-obsidian hover:bg-copper/90"
        >
          {generatingCal ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Calendar className="mr-2 h-4 w-4" />
          )}
          {items.length ? "Regénérer calendrier" : "Générer calendrier"}
        </Button>
        {items.length > 0 ? (
          <Button
            type="button"
            variant="outline"
            className="border-copper/35 text-copper hover:bg-copper/10"
            onClick={handleGenerateAll}
            disabled={!unlocked || generatingAll || generatingCal}
          >
            {generatingAll ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="mr-2 h-4 w-4" />
            )}
            Générer tous les posts
          </Button>
        ) : null}
      </div>

      {items.length > 0 ? (
        <p className="text-xs text-titanium/50">
          {items.length} jalons · {withPosts} avec post(s) · stratégie social mise à jour
        </p>
      ) : null}

      {loading ? (
        <div className="flex h-32 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-copper/40" />
        </div>
      ) : items.length === 0 ? (
        <div className="rounded-xl border border-copper/15 bg-white/[0.02] p-8 text-center text-sm text-titanium/60">
          Aucun calendrier — génère le pipeline internal → launch → post-launch.
        </div>
      ) : (
        <ul className="space-y-3">
          {items.map((item) => (
            <li
              key={item.id}
              className={cn(
                "rounded-xl border p-4",
                PHASE_COLORS[item.phase] ?? "border-white/10 bg-white/[0.02]"
              )}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="mb-1 flex flex-wrap items-center gap-2">
                    <StatusIcon status={item.status} />
                    <span className="rounded-full border border-white/10 px-2 py-0.5 text-[10px] uppercase tracking-wider text-titanium/60">
                      {PHASE_LABELS[item.phase]}
                    </span>
                    <span className="text-xs text-titanium/50">{formatDate(item.planned_at)}</span>
                    {item.content_type ? (
                      <span className="text-[10px] text-titanium/45">
                        {CONTENT_TYPE_LABELS[item.content_type] ?? item.content_type}
                      </span>
                    ) : null}
                  </div>
                  <p className="font-medium text-ivory/90">{item.milestone}</p>
                  {item.notes ? (
                    <p className="mt-1 text-xs leading-relaxed text-titanium/55">{item.notes}</p>
                  ) : null}
                  {item.platforms.length > 0 ? (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {item.platforms.map((p) => {
                        const style = PLATFORM_STYLES[p as PostPlatform];
                        return (
                          <span
                            key={p}
                            className={cn(
                              "rounded-full px-2 py-0.5 text-[10px] ring-1",
                              style?.badge ?? "bg-white/5 text-titanium/60 ring-white/10"
                            )}
                          >
                            {style?.label ?? p}
                          </span>
                        );
                      })}
                    </div>
                  ) : null}
                  {item.post?.text_content ? (
                    <p className="mt-3 rounded-lg border border-white/5 bg-black/20 p-3 text-xs leading-relaxed text-ivory/75">
                      {item.post.text_content.slice(0, 280)}
                      {item.post.text_content.length > 280 ? "…" : ""}
                    </p>
                  ) : null}
                </div>
                {!item.post_id && item.status === "planned" && unlocked ? (
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    className="shrink-0 border-white/10 text-xs"
                    disabled={generatingItem === item.id || generatingAll}
                    onClick={() => void handleGenerateItem(item.id)}
                  >
                    {generatingItem === item.id ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      "Générer post"
                    )}
                  </Button>
                ) : item.post_id ? (
                  <span className="text-[10px] text-emerald-400/80">En approbation</span>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
