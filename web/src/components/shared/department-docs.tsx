"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { BookOpen, ExternalLink, FileText } from "lucide-react";
import { fetchLibraryEntries, type LibraryEntry } from "@/lib/library-api";
import type { BureauKey } from "@/lib/agent-bureau";
import { ROUTES } from "@/lib/routes";
import { cn } from "@/lib/utils";

interface DepartmentDocsProps {
  bureau: BureauKey;
}

type Filter = "all" | "now" | "later";

const FILTERS: { id: Filter; label: string }[] = [
  { id: "all", label: "Tout" },
  { id: "now", label: "Utile maintenant" },
  { id: "later", label: "Pour plus tard" },
];

/**
 * Onglet « Documentation » — les notes réellement archivées pour ce bureau
 * dans la bibliothèque (`GET /library/entries?bureau=…`, alimentée par le
 * vault Obsidian et les recherches des agents). Pas de contenu inventé : un
 * bureau sans note affiche un état vide qui dit où en créer.
 */
export function DepartmentDocs({ bureau }: DepartmentDocsProps) {
  const [entries, setEntries] = useState<LibraryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);
  const [filter, setFilter] = useState<Filter>("all");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setFailed(false);
    fetchLibraryEntries({ bureau, limit: 50 })
      .then((res) => {
        if (!cancelled) setEntries(res.entries ?? []);
      })
      .catch(() => {
        if (!cancelled) {
          setEntries([]);
          setFailed(true);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [bureau]);

  const visible = filter === "all" ? entries : entries.filter((e) => e.timing === filter);

  if (loading) {
    return (
      <div className="grid gap-3 sm:grid-cols-2">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-28 animate-pulse rounded-xl border border-bronze-faint bg-obsidian/50"
          />
        ))}
      </div>
    );
  }

  if (failed) {
    return (
      <div className="rounded-xl border border-red-500/25 bg-red-500/5 px-6 py-8 text-center">
        <p className="text-sm text-red-300">
          La bibliothèque du Hub est injoignable — documentation indisponible.
        </p>
        <button
          type="button"
          onClick={() => setFilter((f) => f)}
          className="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-bronze/40 bg-bronze/10 px-3 py-1.5 text-xs font-semibold text-bronze-bright hover:bg-bronze/20"
        >
          Réessayer
        </button>
      </div>
    );
  }

  if (entries.length === 0) {
    return (
      <div className="rounded-xl border border-bronze-faint bg-obsidian/50 px-6 py-10 text-center">
        <BookOpen className="mx-auto mb-3 h-6 w-6 text-titane/40" />
        <p className="text-sm text-titane/70">Aucune note archivée pour ce bureau.</p>
        <p className="mt-1 text-xs text-titane/45">
          Les recherches des agents et les notes du vault atterrissent ici.
        </p>
        <Link
          href={ROUTES.library}
          className="mt-4 inline-flex items-center gap-1.5 rounded-lg border border-bronze/40 bg-bronze/10 px-3 py-1.5 text-xs font-semibold text-bronze-bright transition-colors hover:bg-bronze/20"
        >
          Ouvrir la bibliothèque
          <ExternalLink className="h-3.5 w-3.5" />
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-1 rounded-lg border border-bronze-faint bg-obsidian-deep/60 p-1">
          {FILTERS.map((f) => (
            <button
              key={f.id}
              type="button"
              onClick={() => setFilter(f.id)}
              className={cn(
                "rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
                filter === f.id
                  ? "bg-copper/12 text-copper-light"
                  : "text-titane/65 hover:text-ivoire",
              )}
            >
              {f.label}
            </button>
          ))}
        </div>
        <Link
          href={ROUTES.library}
          className="inline-flex items-center gap-1.5 text-[11px] text-bronze-bright hover:text-ivoire hover:underline"
        >
          Bibliothèque complète
          <ExternalLink className="h-3 w-3" />
        </Link>
      </div>

      {visible.length === 0 ? (
        <p className="rounded-xl border border-bronze-faint bg-obsidian/50 px-4 py-8 text-center text-xs text-titane/50">
          Aucune note dans ce filtre.
        </p>
      ) : (
        <ul className="grid gap-3 sm:grid-cols-2">
          {visible.map((entry) => (
            <li
              key={entry.id}
              className="rounded-xl border border-bronze-faint bg-obsidian/70 p-4 transition-colors hover:border-bronze/30"
            >
              <div className="flex items-start gap-2.5">
                <FileText className="mt-0.5 h-4 w-4 shrink-0 text-bronze" />
                <div className="min-w-0 flex-1">
                  <h4 className="text-sm font-medium leading-snug text-ivoire/90">
                    {entry.title}
                  </h4>
                  <p className="mt-1.5 line-clamp-3 text-xs leading-relaxed text-titane/60">
                    {entry.summary}
                  </p>
                </div>
                <span
                  className={cn(
                    "shrink-0 rounded-full border px-2 py-0.5 text-[9px] font-medium uppercase tracking-wide",
                    entry.timing === "now"
                      ? "border-copper/30 bg-copper/12 text-copper-glow"
                      : "border-bronze-faint bg-obsidian-deep/60 text-titane/55",
                  )}
                >
                  {entry.timing === "now" ? "Maintenant" : "Plus tard"}
                </span>
              </div>

              {entry.topics.length > 0 || entry.source_url ? (
                <div className="mt-3 flex flex-wrap items-center gap-1.5 border-t border-bronze-faint pt-2.5">
                  {entry.topics.slice(0, 3).map((topic) => (
                    <span
                      key={topic}
                      className="rounded-full border border-bronze-faint bg-obsidian-deep/60 px-2 py-0.5 text-[9px] text-titane/55"
                    >
                      {topic}
                    </span>
                  ))}
                  {entry.source_url ? (
                    <a
                      href={entry.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="ml-auto inline-flex items-center gap-1 text-[10px] text-bronze-bright hover:text-ivoire hover:underline"
                    >
                      Source
                      <ExternalLink className="h-2.5 w-2.5" />
                    </a>
                  ) : null}
                </div>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
