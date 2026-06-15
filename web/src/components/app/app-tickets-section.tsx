"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Loader2, Plus } from "lucide-react";
import { toast } from "sonner";
import { CreateTicketModal } from "@/components/tickets/create-ticket-modal";
import {
  STATUS_STYLES,
  TICKET_STATUSES,
  type TicketStatus,
} from "@/components/tickets/tickets.constants";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchProjects } from "@/lib/api";
import { fetchTicketsList, type TicketWithProject } from "@/lib/tickets";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";

const ACTIVE_STATUSES = new Set<TicketStatus>(["open", "in_progress"]);

interface AppTicketsSectionProps {
  onTicketsChange?: (count: number) => void;
}

export function AppTicketsSection({ onTicketsChange }: AppTicketsSectionProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [tickets, setTickets] = useState<TicketWithProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [allProjects, allTickets] = await Promise.all([
        fetchProjects(),
        fetchTicketsList({ limit: 100 }),
      ]);
      const appProjects = allProjects.filter((p) => p.branch === "app");
      setProjects(appProjects);
      const appIds = new Set(appProjects.map((p) => p.id));
      const appTickets = allTickets.filter((t) => appIds.has(t.project_id));
      setTickets(appTickets);
      onTicketsChange?.(
        appTickets.filter((t) => ACTIVE_STATUSES.has(t.status as TicketStatus)).length
      );
    } catch {
      setTickets([]);
      onTicketsChange?.(0);
    } finally {
      setLoading(false);
    }
  }, [onTicketsChange]);

  useEffect(() => {
    void load();
  }, [load]);

  const activeTickets = tickets.filter((t) =>
    ACTIVE_STATUSES.has(t.status as TicketStatus)
  );

  return (
    <section className="mb-8">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="label-caps">Tickets App</h2>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            className="border-copper/30"
            onClick={() => setCreateOpen(true)}
            disabled={projects.length === 0}
          >
            <Plus className="mr-1 h-3.5 w-3.5" />
            Nouveau ticket
          </Button>
          <Button asChild size="sm" variant="ghost">
            <Link href="/tickets">Tous les tickets</Link>
          </Button>
        </div>
      </div>

      <Card className="border-copper/20 bg-obsidian-2/90">
        <CardHeader className="pb-2">
          <CardTitle className="font-title text-base text-ivory">
            {loading
              ? "Chargement…"
              : `${activeTickets.length} ticket${activeTickets.length !== 1 ? "s" : ""} actif${activeTickets.length !== 1 ? "s" : ""}`}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center gap-2 text-sm text-titanium/60">
              <Loader2 className="h-4 w-4 animate-spin" />
              Chargement des tickets…
            </div>
          ) : tickets.length === 0 ? (
            <p className="text-sm text-titanium/70">
              Aucun ticket pour le moment. Les apps NUAWAY et Naïa ne poussent pas
              encore de tickets automatiquement — crée-en un manuellement si besoin.
            </p>
          ) : (
            <ul className="space-y-2">
              {tickets.slice(0, 12).map((ticket) => {
                const status = ticket.status as TicketStatus;
                const statusClass = STATUS_STYLES[status] ?? STATUS_STYLES.open;
                const statusLabel =
                  TICKET_STATUSES.find((s) => s.id === status)?.label ?? status;
                return (
                  <li key={ticket.id}>
                    <Link
                      href={`/tickets?id=${encodeURIComponent(ticket.id)}`}
                      className={cn(
                        "flex items-center justify-between gap-3 rounded-lg border border-copper/10",
                        "px-3 py-2 text-sm transition hover:border-copper/30 hover:bg-white/[0.02]"
                      )}
                    >
                      <span className="truncate text-ivory/90">{ticket.title}</span>
                      <span className="flex shrink-0 items-center gap-2">
                        <span className="text-xs text-titanium/60">
                          {ticket.project_name ?? "App"}
                        </span>
                        <span
                          className={cn(
                            "rounded border px-1.5 py-0.5 text-[10px] uppercase tracking-wide",
                            statusClass
                          )}
                        >
                          {statusLabel}
                        </span>
                      </span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          )}
        </CardContent>
      </Card>

      <CreateTicketModal
        open={createOpen}
        onOpenChange={setCreateOpen}
        projects={projects}
        defaultProjectId={projects[0]?.id}
        onCreated={() => {
          toast.success("Ticket créé");
          void load();
        }}
      />
    </section>
  );
}
