"use client";

import { useEffect, useState } from "react";
import { fetchTicketsList, type TicketWithProject } from "@/lib/tickets";
import type { Project, ProjectStatus } from "@/lib/types";
import { C } from "./shared";

/* Palette de statut projet, partagée par team.tsx / projects-tab.tsx.
   Les onglets Projets / Missions / Backlog / Documentation vivent chacun
   dans leur propre fichier (projects-tab.tsx / missions-tab.tsx /
   backlog-tab.tsx / documentation-tab.tsx) — assez volumineux pour ne pas
   tenir ici. */

export const PROJECT_PROGRESS: Record<ProjectStatus, number> = {
  paused: 20,
  dev: 45,
  beta: 80,
  active: 100,
};
export const PROJECT_LABEL: Record<ProjectStatus, string> = {
  paused: "En pause",
  dev: "En dev",
  beta: "Bêta",
  active: "Actif",
};
export const PROJECT_COLOR: Record<ProjectStatus, string> = {
  paused: "#9A9089",
  dev: "#A7ADB5",
  beta: C.copperLight,
  active: C.online,
};

/** Chargement des tickets du bureau — partagé par Missions et Backlog. */
export function useBureauTickets(projects: Project[]) {
  const [tickets, setTickets] = useState<TicketWithProject[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (projects.length === 0) {
      setTickets([]);
      setLoading(false);
      return;
    }
    let cancelled = false;
    const ids = new Set(projects.map((p) => p.id));
    fetchTicketsList({ limit: 100 })
      .then((all) => {
        if (!cancelled) setTickets(all.filter((t) => ids.has(t.project_id)));
      })
      .catch(() => {
        if (!cancelled) setTickets([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [projects]);

  return { tickets, loading, setTickets };
}
