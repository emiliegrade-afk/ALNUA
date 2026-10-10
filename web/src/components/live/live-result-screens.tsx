"use client";

import { useState } from "react";
import { AlertTriangle, CheckCircle2, X, XCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { confirmLiveDraft } from "@/lib/live-api";
import type { ResultCard } from "@/lib/live-cards";
import { safeImageSrc } from "@/lib/live-cards-parse";
import { cn } from "@/lib/utils";

import { LiveChartCard } from "./live-chart-card";

interface Props {
  cards: ResultCard[];
  onDismiss: (taskId: string) => void;
}

function CardShell({
  card,
  tone,
  onDismiss,
  children,
}: {
  card: ResultCard;
  tone: "ok" | "error";
  onDismiss: (taskId: string) => void;
  children: React.ReactNode;
}) {
  return (
    <article
      className={cn(
        "rounded-xl border bg-obsidian-2 p-4",
        tone === "error" ? "border-red-500/30" : "border-copper/20",
      )}
    >
      <header className="mb-2 flex items-start justify-between gap-3">
        <h3 className="text-sm font-semibold text-ivory">{card.title}</h3>
        <Button
          variant="ghost"
          size="icon-xs"
          aria-label={`Fermer : ${card.title}`}
          onClick={() => onDismiss(card.taskId)}
        >
          <X />
        </Button>
      </header>
      {children}
    </article>
  );
}

/** Result screens. Everything is rendered as React text: no raw HTML from agents. */
export function LiveResultScreens({ cards, onDismiss }: Props) {
  if (cards.length === 0) {
    return (
      <div className="flex h-full min-h-48 items-center justify-center rounded-xl border border-dashed border-copper/20 text-sm text-zinc-500">
        Les résultats s&apos;affichent ici.
      </div>
    );
  }
  return (
    <div className="grid gap-3 xl:grid-cols-2" aria-label="Écrans de résultats">
      {cards.map((card) => (
        <CardShell key={card.taskId} card={card} tone={card.kind === "error" ? "error" : "ok"} onDismiss={onDismiss}>
          {card.kind === "text" && (
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-ivory/90">
              {card.body}
            </p>
          )}
          {card.kind === "error" && (
            <p className="flex items-start gap-2 text-sm text-red-300">
              <AlertTriangle className="mt-0.5 size-4 shrink-0" />
              {card.message}
            </p>
          )}
          {card.kind === "chart" && <LiveChartCard series={card.series} />}
          {card.kind === "summary" && (
            <div className="space-y-2">
              <p className="text-sm font-medium text-ivory">{card.brief.headline}</p>
              <ul className="list-disc space-y-1 pl-4 text-sm text-ivory/90">
                {card.brief.bullets.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}
          {card.kind === "list" && (
            <div className="space-y-2">
              <p className="text-sm font-medium text-ivory">{card.brief.title}</p>
              <ol className="list-decimal space-y-1 pl-4 text-sm text-ivory/90">
                {card.brief.items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ol>
            </div>
          )}
          {card.kind === "image" && <ImageCard brief={card.brief} />}
          {card.kind === "draft" && <DraftCard brief={card.brief} />}
          {card.kind === "steps" && (
            <div className="space-y-2">
              <p className="text-xs text-copper-light">{card.summary}</p>
              <ul className="space-y-1.5">
                {card.steps.map((step, i) => (
                  <li key={`${step.agent}-${i}`} className="flex items-start gap-2 text-sm">
                    {step.ok ? (
                      <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-400" />
                    ) : (
                      <XCircle className="mt-0.5 size-4 shrink-0 text-red-400" />
                    )}
                    <span className="text-ivory/90">
                      <span className="font-medium text-copper-light">{step.agent}</span>{" "}
                      {step.detail}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardShell>
      ))}
    </div>
  );
}

function ImageCard({ brief }: { brief: Extract<ResultCard, { kind: "image" }>["brief"] }) {
  const src = safeImageSrc(brief.src);
  if (!src) {
    return <p className="text-sm text-zinc-400">{brief.credit || "Image non affichable."}</p>;
  }
  return (
    <figure className="space-y-2">
      {/* Native img: Wikimedia / generated PNG are not in next/image remotePatterns. */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={src}
        alt={brief.title}
        width={640}
        height={640}
        className="max-h-80 w-full rounded-lg object-contain bg-black/40"
      />
      <figcaption className="text-xs text-zinc-400">
        {brief.credit}
        {brief.href.startsWith("https://") ? (
          <>
            {" · "}
            <a href={brief.href} target="_blank" rel="noopener noreferrer" className="text-copper-light underline">
              source
            </a>
          </>
        ) : null}
      </figcaption>
    </figure>
  );
}

function DraftCard({ brief }: { brief: Extract<ResultCard, { kind: "draft" }>["brief"] }) {
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const confirm = async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await confirmLiveDraft(brief.kind, brief.draftId);
      setDone(res.message);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Validation impossible.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-3">
      <p className="text-sm font-medium text-ivory">{brief.title}</p>
      <p className="whitespace-pre-wrap text-sm text-ivory/90">{brief.body}</p>
      {done ? (
        <p className="text-sm text-emerald-300">{done}</p>
      ) : (
        <Button variant="outline" size="sm" disabled={busy} onClick={() => void confirm()}>
          Valider
        </Button>
      )}
      {error ? <p className="text-xs text-red-300">{error}</p> : null}
    </div>
  );
}
