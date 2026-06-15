"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Loader2, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { BureauAgentsSection } from "@/components/shared/bureau-agents-section";
import { DepartmentHeader } from "@/components/shared/department-header";
import { AppConsole } from "@/components/app/app-console";
import { AppTicketsSection } from "@/components/app/app-tickets-section";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { deleteProject, fetchProjects, fetchTickets } from "@/lib/api";
import type { Project } from "@/lib/types";

interface ProjectStat {
  project: Project;
  openTickets: number;
}

export default function AppPolePage() {
  const [projectStats, setProjectStats] = useState<ProjectStat[]>([]);
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const loadProjects = useCallback(async () => {
    setLoadingProjects(true);
    try {
      const projects = await fetchProjects();
      const appProjects = projects.filter((p) => p.branch === "app");
      const stats = await Promise.all(
        appProjects.map(async (project) => {
          const all = await fetchTickets(project.id).catch(() => []);
          const active = all.filter(
            (t) => t.status === "open" || t.status === "in_progress"
          );
          return { project, openTickets: active.length };
        })
      );
      setProjectStats(stats);
    } catch {
      setProjectStats([]);
    } finally {
      setLoadingProjects(false);
    }
  }, []);

  useEffect(() => {
    void loadProjects();
  }, [loadProjects]);

  async function handleDeleteProject(project: Project) {
    if (
      !window.confirm(
        `Supprimer le projet « ${project.name} » ? Cette action est irréversible.`
      )
    ) {
      return;
    }

    setDeletingId(project.id);
    try {
      await deleteProject(project.id);
      toast.success(`Projet « ${project.name} » supprimé`);
      await loadProjects();
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Impossible de supprimer le projet"
      );
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <>
      <BackToLobby />
      <DepartmentHeader
        dept="app"
        title="Pôle App"
        subtitle="NUAWAY · Naïa App · Dev mobile & backend"
      />

      <BureauAgentsSection bureau="app" />

      <AppTicketsSection />

      {loadingProjects ? (
        <p className="mb-8 text-sm text-titanium/60">Chargement des projets…</p>
      ) : projectStats.length > 0 ? (
        <section className="mb-8">
          <h2 className="label-caps mb-4">Projets</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {projectStats.map(({ project, openTickets }) => (
              <Card key={project.id} className="border-copper/20 bg-obsidian-2/90">
                <CardHeader className="pb-2">
                  <CardTitle className="font-title text-base text-ivory">
                    {project.name}
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex items-center justify-between gap-3">
                  <div className="space-y-1">
                    <span className="badge-copper px-2 py-0.5 text-xs">{project.status}</span>
                    <p className="font-body text-sm text-titanium">
                      {openTickets} ticket{openTickets !== 1 ? "s" : ""} actif
                      {openTickets !== 1 ? "s" : ""}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-1">
                    <Button asChild size="sm" variant="ghost">
                      <Link href={`/tickets?project=${encodeURIComponent(project.id)}`}>
                        Ouvrir
                      </Link>
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-titanium/60 hover:text-red-400"
                      disabled={deletingId === project.id}
                      aria-label={`Supprimer ${project.name}`}
                      onClick={() => void handleDeleteProject(project)}
                    >
                      {deletingId === project.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      ) : null}

      <AppConsole />
    </>
  );
}
