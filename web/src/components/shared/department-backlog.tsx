"use client";

import Link from "next/link";
import { useState } from "react";
import { Archive, ArrowRight, Inbox } from "lucide-react";
import { toast } from "sonner";
import {
  PRIORITY_STYLES,
  TYPE_STYLES,
  type TicketPriority,
  type TicketType,
} from "@/components/tickets/tickets.constants";
import { updateTicket, type TicketWithProject } from "@/lib/tickets";
import { ROUTES } from "@/lib/routes";
import { cn } from "@/lib/utils";

interface DepartmentBacklogProps {
  tickets: TicketWithProject[];
  loading: boolean;
  onTicketsChange: (tickets: TicketWithProject[]) => void;
}

/** Ordre d'arbitrage — le backlog se lit du plus urgent au plus accessoire,
 * contrairement au board Missions qui se lit par étape d'avancement. */
const PRIORITY_ORDER: TicketPriority[] = ["critical", "high", "medium", "low"];

function rank(priority: string): number {
  const i = PRIORITY_ORDER.indexOf(priority as TicketPriority);
  return i === -1 ? PRIORITY_ORDER.length : i;
}

/**
 * Onglet « Backlog » — même jeu de tickets que le board Missions, lu comme une
 * file d'attente priorisée : ce qui n'a pas encore démarré (`open`), trié par
 * criticité, plus les demandes écartées (`wont_fix`) reléguées en bas. C'est
 * la vue d'arbitrage ; le board, lui, est la vue de suivi.
 */
export function DepartmentBacklog({
  tickets,
  loading,
  onTicketsChange,
}: DepartmentBacklogProps) {
  const [pendingId, setPendingId] = useState<string | null>(null);

  const queued = tickets
    .filter((t) => t.status === "open")
    .sort((a, b) => rank(a.priority) - rank(b.priority));
  const dropped = tickets.filter((t) => t.status === "wont_fix");

  async function start(ticket: TicketWithProject) {
    if (pendingId === ticket.id) return;
    const previous = tickets;
    setPendingId(ticket.id);
    onTicketsChange(
      tickets.map((t) => (t.id === ticket.id ? { ...t, status: "in_progress" } : t))
    );
    try {
      await updateTicket(ticket.id, { status: "in_progress" });
      toast.success(`« ${ticket.title} » est passé en cours`);
    } catch {
      onTicketsChange(previous);
      toast.error(`Impossible de démarrer « ${ticket.title} »`);
    } finally {
      setPendingId(null);
    }
  }

  if (loading) {
    return (
      <div className="space-y-2">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-16 animate-pulse rounded-xl border border-bronze-faint bg-obsidian/50"
          />
        ))}
      </div>
    );
  }

  if (queued.length === 0 && dropped.length === 0) {
    return (
      <div className="rounded-xl border border-bronze-faint bg-obsidian/50 px-6 py-10 text-center">
        <Inbox className="mx-auto mb-3 h-6 w-6 text-titane/40" />
        <p className="text-sm text-titane/70">Le backlog de ce bureau est vide.</p>
        <p className="mt-1 text-xs text-titane/45">
          Tout ce qui a été demandé est déjà en cours, en revue ou terminé.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section>
        <div className="mb-3 flex items-baseline justify-between gap-3">
          <h3 className="label-caps">
            À arbitrer · {queued.length} demande{queued.length !== 1 ? "s" : ""}
          </h3>
          <Link
            href={ROUTES.tickets}
            className="text-[11px] text-bronze-bright hover:text-ivoire hover:underline"
          >
            Tous les tickets
          </Link>
        </div>

        {queued.length === 0 ? (
          <p className="rounded-xl border border-bronze-faint bg-obsidian/50 px-4 py-6 text-center text-xs text-titane/50">
            Rien en attente d&apos;arbitrage.
          </p>
        ) : (
          <ul className="space-y-2">
            {queued.map((ticket) => {
              const priorityStyle = PRIORITY_STYLES[ticket.priority as TicketPriority];
              const typeStyle = TYPE_STYLES[ticket.type as TicketType];
              return (
                <li
                  key={ticket.id}
                  className="flex flex-wrap items-center gap-3 rounded-xl border border-bronze-faint bg-obsidian/70 px-4 py-3 transition-colors hover:border-bronze/30"
                >
                  <span
                    className={cn(
                      "shrink-0 rounded-full border px-2 py-0.5 text-[9px] font-medium uppercase tracking-wide",
                      priorityStyle?.badge
                    )}
                  >
                    {priorityStyle?.label ?? ticket.priority}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm text-ivoire/90">{ticket.title}</span>
                    <span className="mt-0.5 flex flex-wrap items-center gap-2 text-[10px] text-titane/50">
                      {typeStyle ? <span>{typeStyle.label}</span> : null}
                      {ticket.project_name ? (
                        <>
                          <span className="text-titane/25">·</span>
                          <span>{ticket.project_name}</span>
                        </>
                      ) : null}
                    </span>
                  </span>
                  <button
                    type="button"
                    disabled={pendingId === ticket.id}
                    onClick={() => void start(ticket)}
                    className="inline-flex h-9 shrink-0 items-center gap-1.5 rounded-lg border border-bronze/40 bg-bronze/10 px-3 text-xs font-semibold text-bronze-bright transition-colors hover:bg-bronze/20 disabled:opacity-50"
                  >
                    Démarrer
                    <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      {dropped.length > 0 ? (
        <details className="rounded-xl border border-bronze-faint bg-obsidian/40">
          <summary className="flex cursor-pointer items-center gap-2 px-4 py-3 text-xs text-titane/60 hover:text-ivoire">
            <Archive className="h-3.5 w-3.5" />
            Écartées · {dropped.length}
          </summary>
          <ul className="divide-y divide-bronze-faint border-t border-bronze-faint">
            {dropped.map((ticket) => (
              <li key={ticket.id} className="px-4 py-2.5">
                <p className="truncate text-xs text-titane/55 line-through">{ticket.title}</p>
                {ticket.project_name ? (
                  <p className="mt-0.5 text-[10px] text-titane/35">{ticket.project_name}</p>
                ) : null}
              </li>
            ))}
          </ul>
        </details>
      ) : null}
    </div>
  );
}
