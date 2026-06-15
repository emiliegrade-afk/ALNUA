"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import Link from "next/link";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { BureauAgentsSection } from "@/components/shared/bureau-agents-section";
import { DepartmentHeader } from "@/components/shared/department-header";
import { GddWorkspace } from "@/components/gaming/gdd-workspace";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchProjects } from "@/lib/api";
import { checkNwiroHost } from "@/lib/lobby-api";
import type { Project } from "@/lib/types";

const GamingConsole = dynamic(
  () =>
    import("@/components/gaming/gaming-console").then((m) => ({
      default: m.GamingConsole,
    })),
  {
    loading: () => (
      <p className="text-sm text-titanium/60">Chargement console gaming…</p>
    ),
  }
);

export default function GamingPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [nwiroConnected, setNwiroConnected] = useState(false);

  useEffect(() => {
    fetchProjects()
      .then((all) => setProjects(all.filter((p) => p.branch === "gaming")))
      .catch(() => setProjects([]));
    checkNwiroHost().then(setNwiroConnected);
  }, []);

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

      {projects.length > 0 ? (
        <section className="mb-8">
          <h2 className="label-caps mb-4">Projets</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {projects.map((project) => (
              <Card key={project.id} className="border-copper/20 bg-obsidian-2/90">
                <CardHeader className="pb-2">
                  <CardTitle className="font-title text-base text-ivory">
                    {project.name}
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex items-center justify-between">
                  <span className="badge-copper px-2 py-0.5 text-xs">{project.status}</span>
                  <Button asChild size="sm" variant="ghost">
                    <Link href="/rd">Dossiers R&D</Link>
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      ) : (
        <p className="mb-6 text-sm text-titanium/60">
          Aucun projet gaming en base —{" "}
          <Link href="/rd" className="text-copper hover:underline">
            créer un dossier R&D
          </Link>
          .
        </p>
      )}

      <GddWorkspace projects={projects} />

      <GamingConsole />
    </>
  );
}
