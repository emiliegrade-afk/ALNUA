"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Loader2, Plus } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { CreateTicketModal } from "@/components/tickets/create-ticket-modal";
import { TicketDetailPanel } from "@/components/tickets/ticket-detail-panel";
import { TicketRow } from "@/components/tickets/ticket-row";
import { TicketsHeader } from "@/components/tickets/tickets-header";
import {
  STATUS_TABS,
  type StatusTab,
  type TicketPriority,
  type TicketType,
} from "@/components/tickets/tickets.constants";
import { fetchProjects } from "@/lib/api";
import {
  countOpenTickets,
  fetchTicketsList,
  updateTicket,
  type TicketWithProject,
} from "@/lib/tickets";
import type { Project } from "@/lib/types";

export function TicketsView() {
  const searchParams = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [allTickets, setAllTickets] = useState<TicketWithProject[]>([]);
  const [loading, setLoading] = useState(true);

  const [projectFilter, setProjectFilter] = useState("all");
  const [statusTab, setStatusTab] = useState<StatusTab>("open");
  const [priorityFilter, setPriorityFilter] = useState<TicketPriority[]>([]);
  const [typeFilter, setTypeFilter] = useState<TicketType[]>([]);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);

  const projectMap = useMemo(
    () => Object.fromEntries(projects.map((p) => [p.id, p])),
    [projects]
  );

  const loadTickets = useCallback(async () => {
    setLoading(true);
    try {
      const params: Parameters<typeof fetchTicketsList>[0] = { limit: 100 };
      if (projectFilter !== "all") params.project_id = projectFilter;
      setAllTickets(await fetchTicketsList(params));
    } catch {
      setAllTickets([]);
    } finally {
      setLoading(false);
    }
  }, [projectFilter]);

  useEffect(() => {
    fetchProjects().then(setProjects).catch(() => setProjects([]));
  }, []);

  useEffect(() => {
    const id = searchParams.get("id");
    if (id) setSelectedId(id);
  }, [searchParams]);

  useEffect(() => {
    const projectParam = searchParams.get("project");
    if (!projectParam || projects.length === 0) return;

    const normalized = projectParam.toLowerCase();
    const match = projects.find(
      (p) =>
        p.id === projectParam ||
        p.name.toLowerCase() === normalized ||
        p.name.toLowerCase().replace(/\s+/g, "-") === normalized
    );
    if (match) setProjectFilter(match.id);
  }, [searchParams, projects]);

  useEffect(() => {
    loadTickets();
  }, [loadTickets]);

  const filteredTickets = useMemo(() => {
    const tab = STATUS_TABS.find((t) => t.id === statusTab);
    return allTickets.filter((t) => {
      if (tab?.statuses && !tab.statuses.includes(t.status as never)) {
        return false;
      }
      if (priorityFilter.length && !priorityFilter.includes(t.priority as TicketPriority)) {
        return false;
      }
      if (typeFilter.length && !typeFilter.includes(t.type as TicketType)) {
        return false;
      }
      return true;
    });
  }, [allTickets, statusTab, priorityFilter, typeFilter]);

  const openCount = useMemo(() => countOpenTickets(allTickets), [allTickets]);

  const selectedTicket =
    allTickets.find((t) => t.id === selectedId) ?? null;

  function handleTicketUpdated(updated: TicketWithProject) {
    setAllTickets((prev) =>
      prev.map((t) => (t.id === updated.id ? { ...t, ...updated } : t))
    );
  }

  function handleTicketCreated(ticket: TicketWithProject) {
    setAllTickets((prev) => [ticket, ...prev]);
    setSelectedId(ticket.id);
  }

  async function quickResolve(ticketId: string, e?: React.MouseEvent) {
    e?.stopPropagation();
    try {
      const updated = await updateTicket(ticketId, { status: "done" });
      handleTicketUpdated(updated);
      if (selectedId === ticketId) setSelectedId(null);
      setStatusTab("done");
      toast.success("Ticket marqué comme résolu — visible dans l’onglet Résolus");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur");
    }
  }

  return (
    <div className="relative min-h-[calc(100dvh-8rem)]">
      <TicketsHeader
        projects={projects}
        projectFilter={projectFilter}
        onProjectFilterChange={setProjectFilter}
        statusTab={statusTab}
        onStatusTabChange={setStatusTab}
        priorityFilter={priorityFilter}
        onPriorityFilterChange={setPriorityFilter}
        typeFilter={typeFilter}
        onTypeFilterChange={setTypeFilter}
        openCount={openCount}
        onNewTicket={() => setCreateOpen(true)}
      />

      <div className="mt-6">
        {!loading && filteredTickets.length > 0 && (
          <p className="mb-3 text-xs text-titanium/70">
            Clique sur un ticket pour le détail · Survole une ligne pour le marquer
            résolu rapidement · Le ✕ ferme le panneau sans résoudre le ticket
          </p>
        )}
        {loading ? (
          <div className="flex items-center justify-center py-20 text-titanium">
            <Loader2 className="mr-2 h-5 w-5 animate-spin text-copper" />
            Chargement des tickets…
          </div>
        ) : filteredTickets.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-2xl border border-copper/10 bg-obsidian/50 py-20 text-center ring-1 ring-copper/10">
            <p className="text-sm text-titanium">
              Aucun ticket ici — c&apos;est une bonne nouvelle 🎉
            </p>
            <Button
              onClick={() => setCreateOpen(true)}
              className="mt-4 bg-copper hover:bg-copper-glow"
            >
              <Plus className="mr-2 h-4 w-4" />
              Créer un ticket
            </Button>
          </div>
        ) : (
          <ScrollArea className="h-[calc(100dvh-22rem)] pr-2">
            <ul className="space-y-2">
              {filteredTickets.map((ticket) => (
                <li key={ticket.id}>
                  <TicketRow
                    ticket={ticket}
                    project={projectMap[ticket.project_id]}
                    active={selectedId === ticket.id}
                    onClick={() => setSelectedId(ticket.id)}
                    onPromptClick={(e) => {
                      e.stopPropagation();
                      setSelectedId(ticket.id);
                    }}
                    onResolveClick={(e) => quickResolve(ticket.id, e)}
                  />
                </li>
              ))}
            </ul>
          </ScrollArea>
        )}
      </div>

      <TicketDetailPanel
        ticket={selectedTicket}
        project={
          selectedTicket
            ? projectMap[selectedTicket.project_id]
            : undefined
        }
        open={Boolean(selectedId && selectedTicket)}
        onClose={() => setSelectedId(null)}
        onUpdated={handleTicketUpdated}
        onResolved={() => {
          setStatusTab("done");
          setSelectedId(null);
        }}
      />

      <CreateTicketModal
        open={createOpen}
        onOpenChange={setCreateOpen}
        projects={projects}
        defaultProjectId={
          projectFilter !== "all" ? projectFilter : projects[0]?.id
        }
        onCreated={handleTicketCreated}
        onProjectsUpdated={setProjects}
      />
    </div>
  );
}
