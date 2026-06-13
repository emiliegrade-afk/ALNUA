"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { BureauAgentsSection } from "@/components/shared/bureau-agents-section";
import { DepartmentHeader } from "@/components/shared/department-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchProjects } from "@/lib/api";
import { checkNwiroHost } from "@/lib/lobby-api";
import { useCooStore } from "@/store/coo-store";
import type { Project } from "@/lib/types";

export default function GamingPage() {
  const setPrefillMessage = useCooStore((s) => s.setPrefillMessage);
  const openDrawer = useCooStore((s) => s.openDrawer);
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
    openDrawer();
  }

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

      <BureauAgentsSection
        bureau="gaming"
        mapAgent={(agent) =>
          agent.id === "dev_gaming" && nwiroConnected
            ? { ...agent, badge: "🕹️ Nwiro UE5 connecté" }
            : agent
        }
      />

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
