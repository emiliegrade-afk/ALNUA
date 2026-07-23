"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BookMarked, ChevronRight } from "lucide-react";
import type { BureauKey } from "@/lib/agent-bureau";
import { fetchLibraryEntries } from "@/lib/library-api";
import { ROUTES } from "@/lib/routes";
import {
  BUREAU_LABELS,
  BureauLibraryPanel,
} from "@/components/library/bureau-library-panel";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface BureauLibraryPopupProps {
  bureau?: BureauKey;
  className?: string;
}

/** Compact shelf trigger — opens library in a modal (keeps bureau pages short). */
export function BureauLibraryPopup({ bureau, className }: BureauLibraryPopupProps) {
  const [open, setOpen] = useState(false);
  const [total, setTotal] = useState<number | null>(null);
  const [nowCount, setNowCount] = useState<number | null>(null);

  const label = bureau ? BUREAU_LABELS[bureau] ?? bureau : "ALNUA";

  useEffect(() => {
    let cancelled = false;
    void fetchLibraryEntries({ bureau, limit: 1 })
      .then((res) => {
        if (cancelled) return;
        const count = bureau
          ? res.counts_by_bureau[bureau] ?? res.total
          : res.total;
        setTotal(count);
        setNowCount(res.counts_by_timing?.now ?? 0);
      })
      .catch(() => {
        if (!cancelled) {
          setTotal(null);
          setNowCount(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [bureau, open]);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className={
          className ??
          "mb-6 flex w-full items-center gap-3 rounded-xl border border-copper/20 bg-obsidian-2/70 px-4 py-3 text-left transition hover:border-copper/40 hover:bg-obsidian-2"
        }
      >
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-copper/15 text-copper">
          <BookMarked className="h-4 w-4" />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block font-title text-sm text-ivory">
            Bibliothèque — {label}
          </span>
          <span className="block text-xs text-titanium/55">
            {total === null
              ? "Archives de recherche"
              : total === 0
                ? "Aucune fiche — clique pour ouvrir"
                : `${total} fiche${total !== 1 ? "s" : ""}${
                    nowCount && nowCount > 0 ? ` · ${nowCount} utile(s) maintenant` : ""
                  }`}
          </span>
        </span>
        <ChevronRight className="h-4 w-4 shrink-0 text-titanium/40" />
      </button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent
          className="flex max-h-[min(88vh,820px)] w-[min(96vw,42rem)] max-w-none flex-col gap-0 overflow-hidden border-copper/25 bg-obsidian-2 p-0 text-ivory sm:max-w-none"
          showCloseButton
        >
          <DialogHeader className="shrink-0 border-b border-copper/15 px-5 py-4 pr-12">
            <DialogTitle className="font-title text-base text-ivory">
              Bibliothèque — {label}
            </DialogTitle>
            <DialogDescription className="text-xs text-titanium/60">
              Tout est conservé. Rien n&apos;est supprimé.
            </DialogDescription>
          </DialogHeader>
          <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
            <BureauLibraryPanel bureau={bureau} embedded />
          </div>
          <div className="shrink-0 border-t border-copper/15 px-5 py-3">
            <Link
              href={ROUTES.library}
              className="text-xs text-copper-light hover:underline"
              onClick={() => setOpen(false)}
            >
              Ouvrir la bibliothèque complète →
            </Link>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
