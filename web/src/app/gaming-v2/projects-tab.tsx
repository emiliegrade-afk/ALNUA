"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CreateProjectModal } from "@/components/shared/create-project-modal";
import { fetchLatestGamingBuild } from "@/lib/gaming-builds";
import { fetchModules } from "@/lib/modules";
import type { BureauAgentDef } from "@/lib/agent-bureau";
import type { GamingBuild, Project } from "@/lib/types";
import { C } from "../app-v2/shared";
import { PROJECT_COLOR, PROJECT_LABEL, PROJECT_PROGRESS } from "../app-v2/tabs";

/* version/build/fps/crashes = dernier build ; bugs/features = modules réels. */

function ProjectCard({
  project,
  agents,
  latestBuild,
}: {
  project: Project;
  agents: BureauAgentDef[];
  latestBuild: GamingBuild | null;
}) {
  const prog = PROJECT_PROGRESS[project.status];
  const [bugs, setBugs] = useState<number | null>(null);
  const [featuresPct, setFeaturesPct] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchModules(project.id)
      .then((mods) => {
        if (cancelled) return;
        if (mods.length === 0) {
          setBugs(null);
          setFeaturesPct(null);
          return;
        }
        setBugs(mods.reduce((s, m) => s + (m.open_bugs ?? 0), 0));
        const done = mods.reduce((s, m) => s + (m.features_done ?? 0), 0);
        const total = mods.reduce((s, m) => s + (m.features_total ?? 0), 0);
        setFeaturesPct(total > 0 ? Math.round((done / total) * 100) : null);
      })
      .catch(() => {
        if (!cancelled) {
          setBugs(null);
          setFeaturesPct(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [project.id]);

  return (
    <div className="flex flex-col gap-2.5 dept-instrument p-3.5">
      <div className="flex items-center justify-between gap-2">
        <span className="truncate text-[13.5px] font-semibold" style={{ color: C.ivory }}>
          {project.name}
        </span>
        <span
          className="shrink-0 rounded-full border px-2 py-0.5 text-[8.5px]"
          style={{ borderColor: "rgba(224,155,106,.25)", color: PROJECT_COLOR[project.status] }}
        >
          {PROJECT_LABEL[project.status]}
        </span>
      </div>
      <p className="truncate text-[9.5px]" style={{ color: C.dim }}>
        {project.description || "—"}
      </p>

      <div className="flex items-center gap-2">
        <span className="h-1.5 flex-1 overflow-hidden rounded-full" style={{ background: "rgba(224,155,106,.15)" }}>
          <span
            className="block h-full rounded-full"
            style={{ width: `${prog}%`, background: `linear-gradient(90deg,#B86E45,${C.copperLight})` }}
          />
        </span>
        <span className="text-[11px] font-semibold" style={{ color: C.ivory }}>
          {prog}%
        </span>
      </div>

      <div className="grid grid-cols-3 gap-1.5 border-t pt-2 text-center" style={{ borderColor: C.lineSoft }}>
        <div>
          <p className="text-[13px] font-semibold" style={{ color: C.ivory }}>
            {latestBuild?.game_version ? `v${latestBuild.game_version}` : "—"}
          </p>
          <p className="text-[8px]" style={{ color: C.faint }}>
            Version
          </p>
        </div>
        <div>
          <p className="text-[13px] font-semibold" style={{ color: C.ivory }}>
            {latestBuild ? `#${latestBuild.build_number}` : "—"}
          </p>
          <p className="text-[8px]" style={{ color: C.faint }}>
            Build
          </p>
        </div>
        <div>
          <p
            className="text-[13px] font-semibold"
            style={{
              color:
                latestBuild?.fps_avg == null
                  ? C.ivory
                  : latestBuild.fps_avg >= 60
                    ? C.online
                    : "#f87171",
            }}
          >
            {latestBuild?.fps_avg ?? "—"}
          </p>
          <p className="text-[8px]" style={{ color: C.faint }}>
            FPS moyen
          </p>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-1.5 text-center">
        <div>
          <p
            className="text-[13px] font-semibold"
            style={{ color: (latestBuild?.crashes ?? 0) > 5 ? "#f87171" : C.ivory }}
          >
            {latestBuild?.crashes ?? "—"}
          </p>
          <p className="text-[8px]" style={{ color: C.faint }}>
            Crashs
          </p>
        </div>
        <div>
          <p className="text-[13px] font-semibold" style={{ color: C.ivory }}>
            {bugs ?? "—"}
          </p>
          <p className="text-[8px]" style={{ color: C.faint }}>
            Bugs ouverts
          </p>
        </div>
        <div>
          <p className="text-[13px] font-semibold" style={{ color: C.ivory }}>
            {featuresPct != null ? `${featuresPct}%` : "—"}
          </p>
          <p className="text-[8px]" style={{ color: C.faint }}>
            Features
          </p>
        </div>
      </div>

      <div
        className="flex items-center justify-between border-t pt-2 text-[9.5px]"
        style={{ borderColor: C.lineSoft, color: C.faint }}
      >
        <span>{latestBuild?.branch ?? "branche —"}</span>
        {agents.length > 0 ? <span>{agents.length} agents</span> : null}
      </div>

      <Link
        href={`/projects/${encodeURIComponent(project.id)}`}
        className="rounded-lg border py-1.5 text-center text-[10.5px]"
        style={{ borderColor: "rgba(224,155,106,.22)", color: C.warm }}
      >
        Ouvrir le projet ›
      </Link>
    </div>
  );
}

export function ProjetsTab({
  projects,
  agents,
  onProjectCreated,
}: {
  projects: Project[];
  agents: BureauAgentDef[];
  onProjectCreated: (p: Project) => void;
}) {
  const [createOpen, setCreateOpen] = useState(false);
  const [latestBuilds, setLatestBuilds] = useState<Record<string, GamingBuild | null>>({});

  useEffect(() => {
    let cancelled = false;
    Promise.all(
      projects.map((p) => fetchLatestGamingBuild(p.id).then((b) => [p.id, b] as const).catch(() => [p.id, null] as const))
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
          PROJETS GAMING
        </p>
        <button
          type="button"
          onClick={() => setCreateOpen(true)}
          className="rounded-[18px] border px-3.5 py-1.5 text-[11px]"
          style={{ borderColor: "rgba(224,155,106,.45)", background: "rgba(224,155,106,.12)", color: C.copperLight }}
        >
          ＋ Nouveau projet
        </button>
      </div>

      {projects.length === 0 ? (
        <div className="flex min-h-[200px] flex-1 items-center justify-center rounded-xl border text-[11px]" style={{ borderColor: C.line, color: C.faint }}>
          Aucun projet rattaché au studio Gaming pour le moment.
        </div>
      ) : (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(250px,1fr))] gap-3">
          {projects.map((p) => (
            <ProjectCard key={p.id} project={p} agents={agents} latestBuild={latestBuilds[p.id] ?? null} />
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
