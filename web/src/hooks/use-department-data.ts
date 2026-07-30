"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { CONSOLE_POLL_MS } from "@/components/console/console-provider";
import { fetchProjects } from "@/lib/api";
import { fetchTicketsList, type TicketWithProject } from "@/lib/tickets";
import type { Project, ProjectBranch } from "@/lib/types";
import type { WorkspaceTab } from "@/store/department-workspace-store";

interface DepartmentData {
  projects: Project[];
  projectsLoading: boolean;
  tickets: TicketWithProject[];
  ticketsLoading: boolean;
  refetchTickets: () => Promise<void>;
  /** Local, synchronous mutation — used by MissionsKanban's optimistic
   * update + rollback (must not go through a network round-trip, or the
   * whole point of "instant feedback, roll back on failure" is lost). The
   * next poll cycle reconciles with server truth regardless. */
  setTickets: (tickets: TicketWithProject[]) => void;
}

/**
 * Single source of truth for "projects + tickets, filtered to one bureau" —
 * replaces 3 independent implementations of the same fetch that existed
 * before this hook (app-tickets-section.tsx, app/page.tsx, and what would
 * otherwise have been a 4th copy in ProjectGrid/MissionsKanban).
 *
 * Only fetches/polls the tab that's actually active — no background poll
 * for a tab the user isn't looking at. Data is kept in state across tab
 * switches (not cleared on the "inactive" branch), so switching back to an
 * already-visited tab shows the cached data instantly instead of a fresh
 * loading skeleton.
 */
export function useDepartmentData(
  branch: ProjectBranch | null,
  activeTab: WorkspaceTab
): DepartmentData {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectsLoading, setProjectsLoading] = useState(true);
  const [tickets, setTickets] = useState<TicketWithProject[]>([]);
  const [ticketsLoading, setTicketsLoading] = useState(true);
  const projectIdsRef = useRef<Set<string>>(new Set());

  const loadProjects = useCallback(async () => {
    if (!branch) {
      setProjects([]);
      setProjectsLoading(false);
      return;
    }
    try {
      const all = await fetchProjects();
      const filtered = all.filter((p) => p.branch === branch);
      projectIdsRef.current = new Set(filtered.map((p) => p.id));
      setProjects(filtered);
    } catch {
      toast.error("Impossible de charger les projets");
      setProjects([]);
    } finally {
      setProjectsLoading(false);
    }
  }, [branch]);

  const loadTickets = useCallback(async () => {
    try {
      const all = await fetchTicketsList({ limit: 100 });
      const filtered = branch
        ? all.filter((t) => projectIdsRef.current.has(t.project_id))
        : [];
      setTickets(filtered);
    } catch {
      toast.error("Impossible de charger les missions");
      setTickets([]);
    } finally {
      setTicketsLoading(false);
    }
  }, [branch]);

  // Projets : fetch au premier passage sur l'onglet, puis poll seulement
  // pendant qu'il est actif.
  useEffect(() => {
    if (activeTab !== "projets") return;
    void loadProjects();
    const id = setInterval(() => void loadProjects(), CONSOLE_POLL_MS);
    return () => clearInterval(id);
  }, [activeTab, loadProjects]);

  // Missions et Backlog lisent le même jeu de tickets (deux lectures d'un même
  // sous-ensemble : pipeline vs file d'attente priorisée) — un seul chargement
  // sert les deux onglets. L'onglet Projets en a besoin aussi, pour afficher
  // la charge réelle de chaque projet ("N missions ouvertes").
  useEffect(() => {
    if (activeTab !== "missions" && activeTab !== "backlog" && activeTab !== "projets") {
      return;
    }
    let cancelled = false;
    async function run() {
      if (projectIdsRef.current.size === 0 && branch) {
        await loadProjects();
      }
      if (!cancelled) await loadTickets();
    }
    void run();
    const id = setInterval(() => void loadTickets(), CONSOLE_POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [activeTab, branch, loadProjects, loadTickets]);

  return {
    projects,
    projectsLoading,
    tickets,
    ticketsLoading,
    refetchTickets: loadTickets,
    setTickets,
  };
}
