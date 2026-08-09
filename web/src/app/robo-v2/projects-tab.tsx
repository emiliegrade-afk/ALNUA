"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CreateProjectModal } from "@/components/shared/create-project-modal";
import { fetchBomItems } from "@/lib/pole-api";
import { fetchLatestRoboBuild } from "@/lib/robo-builds";
import type { BureauAgentDef } from "@/lib/agent-bureau";
import type { Project, RoboBuild } from "@/lib/types";
import { C } from "../app-v2/shared";
import { PROJECT_COLOR, PROJECT_LABEL, PROJECT_PROGRESS } from "../app-v2/tabs";

/* version/PCB/firmware/tests passés/anomalies viennent du dernier build
 * réel rapporté (Phase 19, ROADMAP.md, 2026-07-30, robo_builds) — "—" tant
 * qu'aucun build n'a été rapporté. Composants BOM reste branché sur
 * /bom/eve (Phase 11) — seul vrai suivi BOM aujourd'hui, scopé à Eve. */
function ProjectCard({ project, agents, realBomCount, latestBuild }: { project: Project; agents: BureauAgentDef[]; realBomCount: number | null; latestBuild: RoboBuild | null }) {
  const prog = PROJECT_PROGRESS[project.status];
  const bomCount = project.name === "Eve" && realBomCount != null ? realBomCount : null;

  return (
    <div className="flex flex-col gap-2.5 rounded-xl border p-3.5" style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}>
      <div className="flex items-center justify-between gap-2">
        <span className="truncate text-[13.5px] font-semibold" style={{ color: C.ivory }}>
          {project.name}
        </span>
        <span className="shrink-0 rounded-full border px-2 py-0.5 text-[8.5px]" style={{ borderColor: "rgba(192,138,114,.25)", color: PROJECT_COLOR[project.status] }}>
          {PROJECT_LABEL[project.status]}
        </span>
      </div>
      <p className="truncate text-[9.5px]" style={{ color: C.dim }}>
        {project.description || "—"}
      </p>

      <div className="flex items-center gap-2">
        <span className="h-1.5 flex-1 overflow-hidden rounded-full" style={{ background: "rgba(192,138,114,.15)" }}>
          <span className="block h-full rounded-full" style={{ width: `${prog}%`, background: `linear-gradient(90deg,#8A5230,${C.copperLight})` }} />
        </span>
        <span className="text-[11px] font-semibold" style={{ color: C.ivory }}>
          {prog}%
        </span>
      </div>

      <div className="grid grid-cols-3 gap-1.5 border-t pt-2 text-center" style={{ borderColor: C.lineSoft }}>
        <div>
          <p className="text-[13px] font-semibold" style={{ color: C.ivory }}>
            {latestBuild?.version ? `v${latestBuild.version}` : "—"}
          </p>
          <p className="text-[8px]" style={{ color: C.faint }}>
            Version
          </p>
        </div>
        <div>
          <p className="text-[13px] font-semibold" style={{ color: C.ivory }}>
            {latestBuild?.pcb_revision ?? "—"}
          </p>
          <p className="text-[8px]" style={{ color: C.faint }}>
            PCB
          </p>
        </div>
        <div>
          <p className="text-[13px] font-semibold" style={{ color: C.ivory }}>
            {latestBuild?.firmware_version ?? "—"}
          </p>
          <p className="text-[8px]" style={{ color: C.faint }}>
            Firmware
          </p>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-1.5 text-center">
        <div>
          <p className="text-[13px] font-semibold" style={{ color: C.ivory }}>
            {bomCount ?? "—"}
          </p>
          <p className="text-[8px]" style={{ color: C.faint }}>
            Composants BOM
          </p>
        </div>
        <div>
          <p className="text-[13px] font-semibold" style={{ color: (latestBuild?.tests_passed_pct ?? 0) >= 80 ? C.online : "#f87171" }}>
            {latestBuild?.tests_passed_pct ?? "—"}
            {latestBuild?.tests_passed_pct != null ? "%" : ""}
          </p>
          <p className="text-[8px]" style={{ color: C.faint }}>
            Tests passés
          </p>
        </div>
        <div>
          <p className="text-[13px] font-semibold" style={{ color: (latestBuild?.open_issues ?? 0) > 5 ? "#f87171" : C.ivory }}>
            {latestBuild?.open_issues ?? "—"}
          </p>
          <p className="text-[8px]" style={{ color: C.faint }}>
            Anomalies
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between border-t pt-2 text-[9.5px]" style={{ borderColor: C.lineSoft, color: C.faint }}>
        <span>3D · Fusion360</span>
        {agents.length > 0 ? <span>{agents.length} agents</span> : null}
      </div>

      <Link href={`/projects/${encodeURIComponent(project.id)}`} className="rounded-lg border py-1.5 text-center text-[10.5px]" style={{ borderColor: "rgba(192,138,114,.22)", color: C.warm }}>
        Ouvrir le projet ›
      </Link>
    </div>
  );
}

export function ProjetsTab({ projects, agents, onProjectCreated }: { projects: Project[]; agents: BureauAgentDef[]; onProjectCreated: (p: Project) => void }) {
  const [createOpen, setCreateOpen] = useState(false);
  const [realBomCount, setRealBomCount] = useState<number | null>(null);
  const [latestBuilds, setLatestBuilds] = useState<Record<string, RoboBuild | null>>({});

  useEffect(() => {
    let cancelled = false;
    fetchBomItems()
      .then((r) => {
        if (!cancelled) setRealBomCount(r.totals.count);
      })
      .catch(() => {
        if (!cancelled) setRealBomCount(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    Promise.all(
      projects.map((p) => fetchLatestRoboBuild(p.id).then((b) => [p.id, b] as const).catch(() => [p.id, null] as const))
    ).then((entries) => {
      if (!cancelled) setLatestBuilds(Object.fromEntries(entries));
    });
    return () => {
      cancelled = true;
    };
  }, [projects]);

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto pb-2">
      <div className="flex items-center justify-between">
        <p className="text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
          PROJETS ROBOTIQUE
        </p>
        <button
          type="button"
          onClick={() => setCreateOpen(true)}
          className="rounded-[18px] border px-3.5 py-1.5 text-[11px]"
          style={{ borderColor: "rgba(192,138,114,.45)", background: "rgba(192,138,114,.12)", color: C.copperLight }}
        >
          ＋ Nouveau projet
        </button>
      </div>

      {projects.length === 0 ? (
        <div className="flex min-h-[200px] flex-1 items-center justify-center rounded-xl border text-[11px]" style={{ borderColor: C.line, color: C.faint }}>
          Aucun projet rattaché au workshop Robotique pour le moment.
        </div>
      ) : (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(250px,1fr))] gap-3">
          {projects.map((p) => (
            <ProjectCard key={p.id} project={p} agents={agents} realBomCount={realBomCount} latestBuild={latestBuilds[p.id] ?? null} />
          ))}
        </div>
      )}

      <CreateProjectModal
        open={createOpen}
        onOpenChange={setCreateOpen}
        onCreated={(p) => {
          onProjectCreated(p);
          setCreateOpen(false);
        }}
      />
    </div>
  );
}
