"use client";

import { useCallback, useEffect, useState } from "react";
import { BookMarked, ExternalLink, Loader2, Search, Sparkles, Users } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { BureauKey } from "@/lib/agent-bureau";
import {
  fetchLibraryEntries,
  runLibraryResearch,
  type LibraryEntry,
  type LibraryTiming,
} from "@/lib/library-api";

export const BUREAU_LABELS: Record<string, string> = {
  hub: "Direction",
  secretary: "Secrétariat",
  app: "App Dev",
  gaming: "Gaming",
  robo: "Robotics",
  marketing: "Marketing",
  rd: "R&D",
  finances: "Finance",
  analytics: "Analytics",
  academy: "Academy",
};

interface BureauLibraryPanelProps {
  bureau?: BureauKey;
  /** Show research input on full library page only */
  showResearch?: boolean;
  compact?: boolean;
  /** Inside dialog — no outer Card chrome */
  embedded?: boolean;
  className?: string;
}

function TimingBadge({ timing }: { timing: LibraryTiming }) {
  if (timing === "now") {
    return (
      <span className="rounded bg-emerald-500/15 px-1.5 py-0.5 text-[10px] font-medium text-emerald-400">
        Utile maintenant
      </span>
    );
  }
  return (
    <span className="rounded bg-copper/15 px-1.5 py-0.5 text-[10px] font-medium text-copper-light">
      À garder
    </span>
  );
}

export function BureauLibraryPanel({
  bureau,
  showResearch = false,
  compact = false,
  embedded = false,
  className,
}: BureauLibraryPanelProps) {
  const [entries, setEntries] = useState<LibraryEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [timingFilter, setTimingFilter] = useState<LibraryTiming | "all">("all");
  const [query, setQuery] = useState("");
  const [researching, setResearching] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchLibraryEntries({
        bureau,
        timing: timingFilter === "all" ? undefined : timingFilter,
        limit: compact ? 5 : 20,
      });
      setEntries(res.entries);
      setTotal(res.total);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Bibliothèque indisponible");
      setEntries([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [bureau, timingFilter, compact]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleResearch(e: React.FormEvent) {
    e.preventDefault();
    const q = query.trim();
    if (q.length < 3) {
      toast.error("Saisis au moins 3 caractères");
      return;
    }
    setResearching(true);
    try {
      const res = await runLibraryResearch(q, {
        bureaus: bureau ? [bureau] : undefined,
        wait: false,
      });
      toast.success(
        res.message ??
          "Recherche lancée — les fiches apparaîtront dans ~1-3 min."
      );
      setQuery("");
      for (const delayMs of [30_000, 60_000, 120_000, 180_000]) {
        window.setTimeout(() => void load(), delayMs);
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Recherche échouée");
    } finally {
      setResearching(false);
    }
  }

  const title = bureau
    ? `Bibliothèque — ${BUREAU_LABELS[bureau] ?? bureau}`
    : "Bibliothèque ALNUA";

  const body = (
    <div className="space-y-4">
      {showResearch ? (
        <form onSubmit={(e) => void handleResearch(e)} className="flex gap-2">
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ex. dernières sorties IA, UI/UX mobile, Godot 4…"
            className="border-copper/20 bg-obsidian-deep/70 text-sm"
            disabled={researching}
          />
          <Button
            type="submit"
            disabled={researching}
            className="shrink-0 bg-copper text-obsidian hover:bg-copper/90"
          >
            {researching ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <Search className="mr-1 h-3.5 w-3.5" />
                Rechercher
              </>
            )}
          </Button>
        </form>
      ) : null}

      {loading ? (
        <p className="text-sm text-titanium/50">Chargement…</p>
      ) : entries.length === 0 ? (
        <p className="text-sm text-titanium/60">
          Aucune fiche pour l&apos;instant.{" "}
          {showResearch
            ? "Lance une recherche ci-dessus ou demande à Aria/Nadia sur Telegram."
            : "Demande une recherche à Aria ou Nadia — tout sera rangé ici."}
        </p>
      ) : (
        <ul className="space-y-3">
          {entries.map((entry) => (
            <li
              key={entry.id}
              className="rounded-lg border border-copper/10 bg-obsidian-deep/50 p-3"
            >
              <div className="mb-1 flex flex-wrap items-center gap-2">
                <TimingBadge timing={entry.timing} />
                {!bureau ? (
                  <span className="text-[10px] uppercase tracking-wider text-titanium/40">
                    {BUREAU_LABELS[entry.bureau] ?? entry.bureau}
                  </span>
                ) : null}
                <span className="text-[10px] text-titanium/35">
                  {entry.created_at.slice(0, 10)}
                </span>
              </div>
              <p className="font-medium text-sm text-ivory">{entry.title}</p>
              <p className="mt-1 text-xs leading-relaxed text-titanium/70">
                {entry.summary}
              </p>
              {entry.source_url ? (
                <a
                  href={entry.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-2 inline-flex items-center gap-1 text-[11px] text-copper hover:underline"
                >
                  Source
                  <ExternalLink className="h-3 w-3" />
                </a>
              ) : null}
            </li>
          ))}
        </ul>
      )}

      {!compact && total > entries.length ? (
        <p className="text-center text-xs text-titanium/40">
          {entries.length} sur {total} fiches
        </p>
      ) : null}

      {compact && total > 0 && !embedded ? (
        <p className="text-xs text-titanium/50">
          {total} fiche{total !== 1 ? "s" : ""} — voir Bibliothèque complète
        </p>
      ) : null}
    </div>
  );

  if (embedded) {
    return (
      <div className={className}>
        <div className="mb-4 flex justify-end gap-1">
          {(["all", "now", "later"] as const).map((f) => (
            <Button
              key={f}
              size="sm"
              variant={timingFilter === f ? "default" : "ghost"}
              className={
                timingFilter === f
                  ? "h-7 bg-copper/90 text-xs text-obsidian"
                  : "h-7 text-xs text-titanium/60"
              }
              onClick={() => setTimingFilter(f)}
            >
              {f === "all" ? "Tout" : f === "now" ? "Maintenant" : "À garder"}
            </Button>
          ))}
        </div>
        {body}
      </div>
    );
  }

  return (
    <Card className={`border-copper/20 bg-obsidian-2/90 ${className ?? "mb-8"}`}>
      <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
        <div>
          <CardTitle className="flex items-center gap-2 font-title text-base text-ivory">
            <BookMarked className="h-4 w-4 text-copper" />
            {title}
          </CardTitle>
          <p className="label-caps mt-1">
            Recherche · tout est conservé · rien n&apos;est supprimé
          </p>
        </div>
        {!compact ? (
          <div className="flex gap-1">
            {(["all", "now", "later"] as const).map((f) => (
              <Button
                key={f}
                size="sm"
                variant={timingFilter === f ? "default" : "ghost"}
                className={
                  timingFilter === f
                    ? "h-7 bg-copper/90 text-xs text-obsidian"
                    : "h-7 text-xs text-titanium/60"
                }
                onClick={() => setTimingFilter(f)}
              >
                {f === "all" ? "Tout" : f === "now" ? "Maintenant" : "À garder"}
              </Button>
            ))}
          </div>
        ) : null}
      </CardHeader>
      <CardContent>{body}</CardContent>
    </Card>
  );
}

export function LibraryCeoReportCard() {
  const [report, setReport] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleReport() {
    setLoading(true);
    try {
      const { fetchLibraryCeoReport } = await import("@/lib/library-api");
      const res = await fetchLibraryCeoReport(7);
      setReport(res.markdown);
      toast.success("Rapport généré");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Rapport indisponible");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="mb-8 border-copper/20 bg-obsidian-2/90">
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 font-title text-base text-ivory">
          <Sparkles className="h-4 w-4 text-copper" />
          Rapport CEO — Bibliothèque
        </CardTitle>
        <Button
          size="sm"
          variant="outline"
          className="border-copper/20 text-xs"
          disabled={loading}
          onClick={() => void handleReport()}
        >
          {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "Générer"}
        </Button>
      </CardHeader>
      {report ? (
        <CardContent>
          <pre className="whitespace-pre-wrap font-body text-xs leading-relaxed text-titanium/80">
            {report}
          </pre>
        </CardContent>
      ) : null}
    </Card>
  );
}

export function LibraryTeamEnrichCard() {
  const [loading, setLoading] = useState(false);
  const [lastMessage, setLastMessage] = useState<string | null>(null);

  async function handleEnrich() {
    setLoading(true);
    try {
      const { enrichTeamFromLibrary } = await import("@/lib/library-api");
      const res = await enrichTeamFromLibrary({ days: 30, limit: 25 });
      setLastMessage(res.message);
      toast.success(res.message);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Enrichissement indisponible");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="mb-8 border-copper/20 bg-obsidian-2/90">
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle className="flex items-center gap-2 font-title text-base text-ivory">
            <Users className="h-4 w-4 text-copper" />
            Enrichir l&apos;équipe
          </CardTitle>
          <p className="mt-1 font-body text-xs text-titanium/60">
            Diffuse les fiches bibliothèque vers la mémoire de chaque agent (Mem0).
          </p>
        </div>
        <Button
          size="sm"
          className="bg-copper text-obsidian hover:bg-copper-light"
          disabled={loading}
          onClick={() => void handleEnrich()}
        >
          {loading ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            "Diffuser aux agents"
          )}
        </Button>
      </CardHeader>
      {lastMessage ? (
        <CardContent>
          <p className="font-body text-xs text-titanium/75">{lastMessage}</p>
        </CardContent>
      ) : null}
    </Card>
  );
}
