"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { BureauAgentsSection } from "@/components/shared/bureau-agents-section";
import { DepartmentHeader } from "@/components/shared/department-header";
import { AppConsole } from "@/components/app/app-console";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchProjects, fetchTickets } from "@/lib/api";
import type { Project } from "@/lib/types";

interface ProjectStat {
  project: Project;
  openTickets: number;
}

export default function AppPolePage() {
  const [projectStats, setProjectStats] = useState<ProjectStat[]>([]);

  useEffect(() => {
    fetchProjects()
      .then(async (projects) => {
        const appProjects = projects.filter((p) => p.branch === "app");
        const stats = await Promise.all(
          appProjects.map(async (project) => {
            const open = await fetchTickets(project.id, "open").catch(() => []);
            return { project, openTickets: open.length };
          })
        );
        setProjectStats(stats);
      })
      .catch(() => setProjectStats([]));
  }, []);

  return (
    <>
      <BackToLobby />
      <DepartmentHeader
        dept="app"
        title="Pôle App"
        subtitle="Naïa App · Eve Journey · Dev mobile & backend"
      />

      <BureauAgentsSection bureau="app" />

      {projectStats.length > 0 ? (
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
                <CardContent className="flex items-center justify-between">
                  <div className="space-y-1">
                    <span className="badge-copper px-2 py-0.5 text-xs">{project.status}</span>
                    <p className="font-body text-sm text-titanium">
                      {openTickets} ticket{openTickets !== 1 ? "s" : ""} ouvert
                      {openTickets !== 1 ? "s" : ""}
                    </p>
                  </div>
                  <Button asChild size="sm" variant="ghost">
                    <Link href={`/tickets?project=${encodeURIComponent(project.id)}`}>
                      Ouvrir
                    </Link>
                  </Button>
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
