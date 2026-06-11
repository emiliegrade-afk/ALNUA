"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AgentCard } from "@/components/shared/agent-card";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { DepartmentHeader } from "@/components/shared/department-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchProjects } from "@/lib/api";
import { checkNwiroHost } from "@/lib/lobby-api";
import { useCooStore } from "@/store/coo-store";
import { useRouter } from "next/navigation";
import type { Project } from "@/lib/types";

export default function GamingPage() {
  const router = useRouter();
  const setPrefillMessage = useCooStore((s) => s.setPrefillMessage);
  const [projects, setProjects] = useState<Project[]>([]);
  const [nwiroConnected, setNwiroConnected] = useState(false);

  useEffect(() => {
    fetchProjects()
      .then((all) => setProjects(all.filter((p) => p.branch === "gaming")))
      .catch(() => setProjects([]));
    checkNwiroHost().then(setNwiroConnected);
  }, []);

  function generateQuest() {
    setPrefillMessage("Génère une quête pour Wyrdheim Online");
    router.push("/ceo");
  }

  const gamingAgents = [
    {
      icon: "🎬",
      name: "Game Director",
      role: "Direction créative",
      branch: "gaming" as const,
      description: "Lore, quêtes et vision narrative Wyrdheim.",
      skills: ["Lore", "Quêtes", "Narration"],
    },
    {
      icon: "🕹️",
      name: "Dev Gaming",
      role: "Développement UE5",
      branch: "gaming" as const,
      description: "Intégration UE5, Nwiro et builds gaming.",
      skills: ["UE5", "Nwiro", "C++"],
      badge: nwiroConnected ? "🕹️ Nwiro UE5 connecté" : undefined,
    },
    {
      icon: "📣",
      name: "Marketing Gaming",
      role: "Communauté",
      branch: "gaming" as const,
      description: "Discord, trailers et communication Wyrdheim.",
      skills: ["Discord", "Trailers", "Community"],
    },
  ];

  const displayProjects =
    projects.length > 0
      ? projects
      : [
          { id: "wyrdheim", name: "Wyrdheim Online", status: "rd" },
          { id: "naia-world", name: "Naïa World", status: "rd" },
        ];

  return (
    <>
      <BackToLobby />
      <DepartmentHeader
        dept="gaming"
        title="Pôle Gaming"
        subtitle="Wyrdheim Online · Naïa World · UE5 · Lore"
      />

      <section className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {gamingAgents.map((agent) => (
          <AgentCard key={agent.name} {...agent} />
        ))}
      </section>

      <section className="mb-8">
        <h2 className="label-caps mb-4">Projets</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {displayProjects.map((project) => (
            <Card
              key={project.id}
              className="border-copper/20 bg-obsidian-2/90"
            >
              <CardHeader className="pb-2">
                <CardTitle className="font-title text-base text-ivory">
                  {project.name}
                </CardTitle>
                <p className="font-body text-xs text-titanium/60">
                  {"name" in project && project.name === "Wyrdheim Online"
                    ? "MMORPG fantasy nordique"
                    : "Monde 3D ouvert"}
                </p>
              </CardHeader>
              <CardContent>
                <span className="badge-copper px-2 py-0.5 text-xs">
                  {project.status === "rd" ? "R&D" : project.status}
                </span>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section>
        <h2 className="label-caps mb-4">Outils Gaming</h2>
        <div className="flex flex-wrap gap-3">
          <Button asChild variant="outline" className="border-copper/30 hover:border-copper/50">
            <Link href="/brainstorm">Lore Database</Link>
          </Button>
          <Button
            variant="outline"
            className="border-copper/30 hover:border-copper/50"
            onClick={generateQuest}
          >
            Générer une quête
          </Button>
          <Button asChild variant="outline" className="border-copper/30 hover:border-copper/50">
            <a
              href="https://discord.gg"
              target="_blank"
              rel="noopener noreferrer"
            >
              Discord Wyrdheim
            </a>
          </Button>
        </div>
      </section>
    </>
  );
}
