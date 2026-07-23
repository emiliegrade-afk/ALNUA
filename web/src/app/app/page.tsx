"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Loader2, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { BureauAgentsSection } from "@/components/shared/bureau-agents-section";
import { BureauPage } from "@/components/shared/bureau-page";
import { BureauPanel } from "@/components/shared/bureau-panel";
import { AppConsole } from "@/components/app/app-console";
import { AppTicketsSection } from "@/components/app/app-tickets-section";
import { Button } from "@/components/ui/button";
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
    <BureauPage
      dept="app"
      title="Pôle App"
      subtitle="App Office · Dev mobile & backend"
    >
      <p className="rounded-xl border border-bronze-faint bg-obsidian/70 px-4 py-3 font-body text-sm text-titane/80">
        Pour lier tes repos GitHub ou lancer une nouvelle app (Factory) :{" "}
        <Link href="/apps" className="text-bronze-bright underline hover:text-ivoire">
          Mes apps
        </Link>
      </p>

      <BureauAgentsSection bureau="app" />
      <AppTicketsSection />

      {loadingProjects ? (
        <p className="text-sm text-titane/60">Chargement des projets…</p>
      ) : projectStats.length > 0 ? (
        <section>
          <h2 className="label-caps mb-4">Projets</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {projectStats.map(({ project, openTickets }) => (
              <BureauPanel key={project.id} title={project.name}>
                <div className="flex items-center justify-between gap-3">
                  <div className="space-y-1">
                    <span className="rounded-full border border-bronze-faint bg-bronze/10 px-2 py-0.5 text-xs text-bronze-bright">
                      {project.status}
                    </span>
                    <p className="font-body text-sm text-titane/80">
                      {openTickets} ticket{openTickets !== 1 ? "s" : ""} actif
                      {openTickets !== 1 ? "s" : ""}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-1">
                    <Button asChild size="sm" variant="ghost" className="text-bronze-bright">
                      <Link href={`/tickets?project=${encodeURIComponent(project.id)}`}>
                        Ouvrir
                      </Link>
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-titane/60 hover:text-red-400"
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
                </div>
              </BureauPanel>
            ))}
          </div>
        </section>
      ) : null}

      <AppConsole />
    </BureauPage>
  );
}
