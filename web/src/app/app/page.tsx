"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ExternalLink } from "lucide-react";
import { AgentCard } from "@/components/shared/agent-card";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { DepartmentHeader } from "@/components/shared/department-header";
import { AgentFocusPanel } from "@/components/openroom/agent-focus-panel";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchProjects, fetchTickets } from "@/lib/api";
import { fetchAgentsStatus, type AgentStatus } from "@/lib/openroom-api";
import { useCooStore } from "@/store/coo-store";
import type { Project } from "@/lib/types";

const POLL_MS = 3000;

const APP_AGENTS = [
  {
    id: "dev_app",
    icon: "💻",
    name: "Dev App Agent",
    role: "Développement",
    branch: "app" as const,
    description: "Développement Naïa App et Eve Journey.",
    skills: ["React Native", "API", "Pipeline"],
  },
  {
    id: "content",
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
  const setPrefillMessage = useCooStore((s) => s.setPrefillMessage);
  const openDrawer = useCooStore((s) => s.openDrawer);
  const [projectStats, setProjectStats] = useState<ProjectStat[]>([]);
  const [focusedAgentId, setFocusedAgentId] = useState<string | null>(null);
  const [agentStatuses, setAgentStatuses] = useState<Record<string, AgentStatus>>({});

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

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      const data = await fetchAgentsStatus();
      if (cancelled) return;
      setAgentStatuses(data.agents);
    }

    void poll();
    const interval = setInterval(() => void poll(), POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  function launchPipeline() {
    setPrefillMessage("Lance le pipeline sur une issue Naïa");
    openDrawer();
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
          <AgentCard
            key={agent.id}
            {...agent}
            status={agentStatuses[agent.id]?.status ?? "idle"}
            currentTask={agentStatuses[agent.id]?.currentTask}
            onClick={() => setFocusedAgentId(agent.id)}
          />
        ))}
      </section>

      <section className="mb-8">
        <h2 className="label-caps mb-4">Projets</h2>
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
        <h2 className="label-caps mb-4">Actions rapides</h2>
        <div className="flex flex-wrap gap-3">
          <Button asChild variant="outline" className="border-copper/30 hover:border-copper/50">
            <Link href="/tickets">Voir les tickets Naïa</Link>
          </Button>
          <Button
            variant="outline"
            className="border-copper/30 hover:border-copper/50"
            onClick={launchPipeline}
          >
            Lancer pipeline
          </Button>
          <Button asChild variant="outline" className="border-copper/30 hover:border-copper/50">
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

      {focusedAgentId ? (
        <AgentFocusPanel
          agent={{
            id: focusedAgentId,
            name: APP_AGENTS.find((a) => a.id === focusedAgentId)!.name,
            emoji: APP_AGENTS.find((a) => a.id === focusedAgentId)!.icon,
            role: APP_AGENTS.find((a) => a.id === focusedAgentId)!.role,
          }}
          status={agentStatuses[focusedAgentId] ?? { status: "idle" }}
          onClose={() => setFocusedAgentId(null)}
        />
      ) : null}
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
    <Card className="border-copper/20 bg-obsidian-2/90">
      <CardHeader className="pb-2">
        <CardTitle className="font-title text-base text-ivory">{name}</CardTitle>
      </CardHeader>
      <CardContent className="flex items-center justify-between">
        <div className="space-y-1">
          <span className="badge-copper px-2 py-0.5 text-xs">
            {status}
          </span>
          <p className="font-body text-sm text-titanium">
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
