"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ExternalLink } from "lucide-react";
import { AgentCard } from "@/components/shared/agent-card";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { DepartmentHeader } from "@/components/shared/department-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchProjects, fetchTickets } from "@/lib/api";
import { useCooStore } from "@/store/coo-store";
import { useRouter } from "next/navigation";
import type { Project } from "@/lib/types";

const APP_AGENTS = [
  {
    icon: "💻",
    name: "Dev App Agent",
    role: "Développement",
    branch: "app" as const,
    description: "Développement Naïa App et Eve Journey.",
    skills: ["React Native", "API", "Pipeline"],
  },
  {
    icon: "✍️",
    name: "Content Agent",
    role: "Contenu",
    branch: "app" as const,
    description: "Posts, dev logs et contenu produit.",
    skills: ["Copywriting", "SEO", "Social"],
  },
];

interface ProjectStat {
  project: Project;
  openTickets: number;
}

export default function AppPolePage() {
  const router = useRouter();
  const setPrefillMessage = useCooStore((s) => s.setPrefillMessage);
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

  function launchPipeline() {
    setPrefillMessage("Lance le pipeline sur une issue Naïa");
    router.push("/ceo");
  }

  return (
    <>
      <BackToLobby />
      <DepartmentHeader
        dept="app"
        title="Pôle App"
        subtitle="Naïa App · Eve Journey · Dev · Content"
      />

      <section className="mb-8 grid gap-4 sm:grid-cols-2">
        {APP_AGENTS.map((agent) => (
          <AgentCard key={agent.name} {...agent} />
        ))}
      </section>

      <section className="mb-8">
        <h2 className="mb-4 text-sm font-medium uppercase tracking-widest text-gray-500">
          Projets
        </h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {projectStats.length === 0 ? (
            <>
              <ProjectCard
                name="Naïa App"
                status="Beta"
                tickets={0}
                href="/tickets?project=naia"
              />
              <ProjectCard
                name="Eve Journey"
                status="Dev"
                tickets={0}
                href="/tickets"
              />
            </>
          ) : (
            projectStats.map(({ project, openTickets }) => (
              <ProjectCard
                key={project.id}
                name={project.name}
                status={project.status}
                tickets={openTickets}
                href={`/tickets?project=${encodeURIComponent(project.name.toLowerCase())}`}
              />
            ))
          )}
        </div>
      </section>

      <section>
        <h2 className="mb-4 text-sm font-medium uppercase tracking-widest text-gray-500">
          Actions rapides
        </h2>
        <div className="flex flex-wrap gap-3">
          <Button asChild variant="outline" className="border-green-500/30">
            <Link href="/tickets">Voir les tickets Naïa</Link>
          </Button>
          <Button
            variant="outline"
            className="border-green-500/30"
            onClick={launchPipeline}
          >
            Lancer pipeline
          </Button>
          <Button asChild variant="outline" className="border-green-500/30">
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2"
            >
              Voir les PRs
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </Button>
        </div>
      </section>
    </>
  );
}

function ProjectCard({
  name,
  status,
  tickets,
  href,
}: {
  name: string;
  status: string;
  tickets: number;
  href: string;
}) {
  return (
    <Card className="border-green-500/20 bg-[#111827]/80">
      <CardHeader className="pb-2">
        <CardTitle className="text-base text-white">{name}</CardTitle>
      </CardHeader>
      <CardContent className="flex items-center justify-between">
        <div className="space-y-1">
          <span className="rounded-full bg-green-500/10 px-2 py-0.5 text-xs text-green-400">
            {status}
          </span>
          <p className="text-sm text-gray-400">
            {tickets} ticket{tickets !== 1 ? "s" : ""} ouvert{tickets !== 1 ? "s" : ""}
          </p>
        </div>
        <Button asChild size="sm" variant="ghost">
          <Link href={href}>Ouvrir</Link>
        </Button>
      </CardContent>
    </Card>
  );
}
