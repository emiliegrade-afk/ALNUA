"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import Link from "next/link";
import { BureauAgentsSection } from "@/components/shared/bureau-agents-section";
import { BureauPage } from "@/components/shared/bureau-page";
import { BureauPanel } from "@/components/shared/bureau-panel";
import { GddWorkspace } from "@/components/gaming/gdd-workspace";
import { Button } from "@/components/ui/button";
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
    <BureauPage
      dept="gaming"
      title="Pôle Gaming"
      subtitle="Wyrdheim Online · Naïa World · UE5 · Lore"
    >
      <BureauAgentsSection
        bureau="gaming"
        mapAgent={(agent) =>
          agent.id === "dev_gaming" && nwiroConnected
            ? { ...agent, badge: "🕹️ Nwiro UE5 connecté" }
            : agent
        }
      />

      {projects.length > 0 ? (
        <section>
          <h2 className="label-caps mb-4">Projets</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {projects.map((project) => (
              <BureauPanel key={project.id} title={project.name}>
                <div className="flex items-center justify-between">
                  <span className="rounded-full border border-bronze-faint bg-bronze/10 px-2 py-0.5 text-xs text-bronze-bright">
                    {project.status}
                  </span>
                  <Button asChild size="sm" variant="ghost" className="text-bronze-bright">
                    <Link href="/rd">Dossiers R&D</Link>
                  </Button>
                </div>
              </BureauPanel>
            ))}
          </div>
        </section>
      ) : (
        <p className="text-sm text-titane/60">
          Aucun projet gaming en base —{" "}
          <Link href="/rd" className="text-bronze-bright hover:underline">
            créer un dossier R&D
          </Link>
          .
        </p>
      )}

      <GddWorkspace projects={projects} />
      <GamingConsole />
    </BureauPage>
  );
}
