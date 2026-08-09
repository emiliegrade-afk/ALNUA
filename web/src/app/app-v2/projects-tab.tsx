"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { LayoutGrid, List, SlidersHorizontal } from "lucide-react";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { CreateProjectModal } from "@/components/shared/create-project-modal";
import { ROUTES } from "@/lib/routes";
import type { TicketWithProject } from "@/lib/tickets";
import type { ConsoleActivityItem } from "@/lib/console/types";
import type { BureauAgentDef } from "@/lib/agent-bureau";
import type { Project, ProjectStatus } from "@/lib/types";
import { C, KIND_META } from "./shared";
import { PROJECT_COLOR, PROJECT_LABEL, PROJECT_PROGRESS } from "./tabs";

/* Tableau de bord "Projets" — maquette dédiée (distincte de la maquette
   "APP Department" d'origine), reproduite à l'identique hors barre
   supérieure. Les vignettes projet sont un dégradé de secours en attendant
   les logos réels (équipe Brand Design) : un `image_url` sur `Project`
   suffira à les remplacer plus tard, pas de retouche structurelle attendue.

   Le pipeline 5 étapes (IDÉE/DESIGN/DEV/QA/RELEASE) et les statuts filtrés
   n'existent pas comme tels côté backend — dérivés du seul champ réel
   `status` (paused/dev/beta/active). "MAJ", "Tâches", "Agents impliqués" et
   le donut de répartition sont calculés à partir des tickets/agents réels. */

const NAME_ICONS = ["✦", "◆", "✧", "◈", "❖", "✶"];

function nameIcon(seed: string) {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) % NAME_ICONS.length;
  return NAME_ICONS[h];
}

/** "Sprint N" n'existe pas comme tel côté backend (pas de cycles suivis) —
 * dérivé du temps réel écoulé depuis la création du projet (1 sprint = 1
 * semaine), pas un numéro inventé au hasard. */
function sprintNumber(createdAt: string) {
  const weeks = Math.floor((Date.now() - new Date(createdAt).getTime()) / (7 * 86_400_000));
  return Math.max(1, weeks + 1);
}

const STAGES = ["IDÉE", "DESIGN", "DEV", "QA", "RELEASE"] as const;
const STAGE_INDEX: Record<ProjectStatus, number> = {
  paused: 0,
  dev: 2,
  beta: 3,
  active: 4,
};

const STATUS_FILTERS: { key: "all" | ProjectStatus; label: string }[] = [
  { key: "all", label: "Tous" },
  { key: "active", label: PROJECT_LABEL.active },
  { key: "beta", label: PROJECT_LABEL.beta },
  { key: "dev", label: PROJECT_LABEL.dev },
  { key: "paused", label: PROJECT_LABEL.paused },
];

/** Dégradé déterministe par projet (hash du nom) — pas une vraie image,
 * juste une texture stable le temps que les logos réels arrivent. */
function placeholderGradient(seed: string) {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) % 360;
  return `radial-gradient(120% 140% at 20% 0%, hsla(${h},35%,22%,.9), rgba(10,9,8,.95) 65%), radial-gradient(90% 90% at 100% 100%, hsla(${(h + 40) % 360},30%,18%,.8), transparent 60%)`;
}

function relTime(iso: string) {
  const diffMs = Date.now() - new Date(iso).getTime();
  const min = Math.floor(diffMs / 60_000);
  if (min < 1) return "à l'instant";
  if (min < 60) return `il y a ${min} min`;
  const h = Math.floor(min / 60);
  if (h < 24) return `il y a ${h} h`;
  return `il y a ${Math.floor(h / 24)} j`;
}

function inWindow(iso: string, daysAgoStart: number, daysAgoEnd: number) {
  const t = new Date(iso).getTime();
  const now = Date.now();
  const day = 86_400_000;
  return t >= now - daysAgoStart * day && t < now - daysAgoEnd * day;
}

function DonutChart({ segments }: { segments: { color: string; count: number }[] }) {
  const total = segments.reduce((s, seg) => s + seg.count, 0);
  const r = 46;
  const circ = 2 * Math.PI * r;
  let acc = 0;
  return (
    <svg width="120" height="120" viewBox="0 0 120 120">
      <circle cx="60" cy="60" r={r} fill="none" stroke="rgba(192,138,114,.1)" strokeWidth="14" />
      {total > 0
        ? segments
            .filter((seg) => seg.count > 0)
            .map((seg, i) => {
              const frac = seg.count / total;
              const dash = `${(frac * circ).toFixed(2)} ${circ.toFixed(2)}`;
              const offset = -acc * circ;
              acc += frac;
              return (
                <circle
                  key={i}
                  cx="60"
                  cy="60"
                  r={r}
                  fill="none"
                  stroke={seg.color}
                  strokeWidth="14"
                  strokeDasharray={dash}
                  strokeDashoffset={offset}
                  transform="rotate(-90 60 60)"
                />
              );
            })
        : null}
      <text x="60" y="56" textAnchor="middle" fontSize="26" fontWeight="600" fill={C.ivory}>
        {total}
      </text>
      <text x="60" y="74" textAnchor="middle" fontSize="9.5" fill={C.faint}>
        Projets
      </text>
    </svg>
  );
}

function ProjectCard({
  project,
  tickets,
  agents,
}: {
  project: Project;
  tickets: TicketWithProject[];
  agents: BureauAgentDef[];
}) {
  const projectTickets = useMemo(
    () => tickets.filter((t) => t.project_id === project.id),
    [tickets, project.id],
  );
  const taskCount = projectTickets.length;
  const majCount = projectTickets.filter((t) => inWindow(t.updated_at, 14, 0)).length;
  const lastTicket = [...projectTickets].sort(
    (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
  )[0];
  const prog = PROJECT_PROGRESS[project.status];
  const stageIdx = STAGE_INDEX[project.status];
  const team = agents.slice(0, 3);
  const extra = Math.max(0, agents.length - team.length);

  return (
    <div
      className="flex flex-col overflow-hidden rounded-xl border"
      style={{ borderColor: C.line, background: "rgba(19,22,27,.55)" }}
    >
      <div
        className="relative flex h-[92px] shrink-0 flex-col justify-end p-3"
        style={{ background: placeholderGradient(project.id) }}
      >
        <p className="flex items-center gap-1.5 truncate text-[14px] font-semibold" style={{ color: C.ivory }}>
          {project.name}
          <span className="text-[11px]" style={{ color: C.copperLight }}>
            {nameIcon(project.id)}
          </span>
        </p>
        <p className="truncate text-[9.5px]" style={{ color: C.warm }}>
          {project.description || PROJECT_LABEL[project.status]}
        </p>
      </div>

      <div className="flex flex-col gap-2.5 p-3">
        <div className="flex items-center gap-2.5">
          <div className="relative h-[42px] w-[42px] shrink-0">
            <svg width="42" height="42" viewBox="0 0 42 42">
              <circle cx="21" cy="21" r="17" fill="none" stroke="rgba(192,138,114,.15)" strokeWidth="3.5" />
              <circle
                cx="21"
                cy="21"
                r="17"
                fill="none"
                stroke={PROJECT_COLOR[project.status]}
                strokeWidth="3.5"
                strokeLinecap="round"
                strokeDasharray={`${((prog / 100) * 2 * Math.PI * 17).toFixed(1)} ${(2 * Math.PI * 17).toFixed(1)}`}
                transform="rotate(-90 21 21)"
              />
            </svg>
            <span
              className="absolute inset-0 flex items-center justify-center text-[10px] font-semibold"
              style={{ color: C.ivory }}
            >
              {prog}%
            </span>
          </div>
          <span className="min-w-0 flex-1">
            <span className="block text-[10.5px] font-medium" style={{ color: PROJECT_COLOR[project.status] }}>
              {PROJECT_LABEL[project.status]}
            </span>
            <span className="block text-[8.5px]" style={{ color: C.faint }}>
              Sprint {sprintNumber(project.created_at)}
            </span>
          </span>
        </div>

        <div className="flex items-center gap-[3px]">
          {STAGES.map((stage, i) => (
            <span key={stage} className="flex flex-1 flex-col items-center gap-1">
              <span
                className="h-[6px] w-[6px] rounded-full"
                style={{
                  background: i <= stageIdx ? C.copper : "rgba(192,138,114,.18)",
                  boxShadow: i === stageIdx ? `0 0 5px ${C.copper}` : undefined,
                }}
              />
              <span
                className="text-[7px] tracking-[0.5px]"
                style={{ color: i === stageIdx ? C.copperLight : C.faint }}
              >
                {stage}
              </span>
            </span>
          ))}
        </div>

        <div className="grid grid-cols-3 gap-1.5 border-t pt-2" style={{ borderColor: C.lineSoft }}>
          <div className="text-center">
            <p className="text-[13px] font-semibold" style={{ color: C.ivory }}>
              {agents.length}
            </p>
            <p className="text-[8px]" style={{ color: C.faint }}>
              Agents
            </p>
          </div>
          <div className="text-center">
            <p className="text-[13px] font-semibold" style={{ color: C.ivory }}>
              {taskCount}
            </p>
            <p className="text-[8px]" style={{ color: C.faint }}>
              Tâches
            </p>
          </div>
          <div className="text-center">
            <p className="text-[13px] font-semibold" style={{ color: C.ivory }}>
              {majCount}
            </p>
            <p className="text-[8px]" style={{ color: C.faint }}>
              MAJ
            </p>
          </div>
        </div>

        <div className="border-t pt-2" style={{ borderColor: C.lineSoft }}>
          <p className="text-[8px]" style={{ color: C.faint }}>
            Dernière activité {lastTicket ? relTime(lastTicket.updated_at) : ""}
          </p>
          <p className="mt-0.5 truncate text-[10px]" style={{ color: C.warm }}>
            {lastTicket ? lastTicket.title : "Aucun ticket pour ce projet."}
          </p>
          {team.length > 0 ? (
            <div className="mt-1.5 flex items-center gap-2">
              <span className="flex shrink-0 -space-x-1.5">
                {team.map((a) => (
                  <span
                    key={a.id}
                    className="rounded-full ring-2"
                    style={{ boxShadow: "0 0 0 2px #100F0D" }}
                    title={a.name}
                  >
                    <AgentAvatar agentId={a.id} name={a.name} size={20} />
                  </span>
                ))}
                {extra > 0 ? (
                  <span
                    className="flex h-5 w-5 items-center justify-center rounded-full text-[8px]"
                    style={{ background: "rgba(192,138,114,.18)", color: C.warm, boxShadow: "0 0 0 2px #100F0D" }}
                  >
                    +{extra}
                  </span>
                ) : null}
              </span>
              <p className="min-w-0 flex-1 truncate text-[8.5px]" style={{ color: C.faint }}>
                {team.map((a) => a.name.split(" ")[0]).join(", ")}
                {extra > 0 ? ` +${extra}` : ""}
              </p>
            </div>
          ) : null}
        </div>

        <Link
          href={`/projects/${encodeURIComponent(project.id)}`}
          className="rounded-lg border py-1.5 text-center text-[10.5px]"
          style={{ borderColor: "rgba(192,138,114,.22)", color: C.warm }}
        >
          Ouvrir le projet ›
        </Link>
      </div>
    </div>
  );
}

function ProjectListRow({
  project,
  tickets,
  onDelete,
  deleting,
}: {
  project: Project;
  tickets: TicketWithProject[];
  onDelete?: (project: Project) => void;
  deleting?: boolean;
}) {
  const taskCount = tickets.filter((t) => t.project_id === project.id).length;
  const prog = PROJECT_PROGRESS[project.status];
  return (
    <div
      className="flex items-center gap-3 rounded-lg border px-3 py-2.5"
      style={{ borderColor: C.line }}
    >
      <Link
        href={`/projects/${encodeURIComponent(project.id)}`}
        className="flex min-w-0 flex-1 items-center gap-3 transition-colors hover:opacity-80"
      >
        <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: PROJECT_COLOR[project.status] }} />
        <span className="min-w-0 flex-1 truncate text-[12px] font-medium" style={{ color: C.ivory }}>
          {project.name}
        </span>
        <span className="w-24 shrink-0 text-[10px]" style={{ color: PROJECT_COLOR[project.status] }}>
          {PROJECT_LABEL[project.status]}
        </span>
        <span className="w-16 shrink-0 text-[10px]" style={{ color: C.dim }}>
          {taskCount} tâches
        </span>
        <span className="w-10 shrink-0 text-right text-[11px] font-semibold" style={{ color: C.ivory }}>
          {prog}%
        </span>
      </Link>
      {onDelete ? (
        <button
          type="button"
          onClick={() => onDelete(project)}
          disabled={deleting}
          className="shrink-0 rounded-lg border px-2 py-1 text-[10px] disabled:opacity-50"
          style={{ borderColor: "rgba(248,113,113,.25)", color: "#f87171" }}
          aria-label={`Supprimer ${project.name}`}
        >
          {deleting ? "…" : "✕"}
        </button>
      ) : null}
    </div>
  );
}

export function ProjetsTab({
  projects,
  tickets,
  activityFeed,
  agents,
  onProjectCreated,
  onDeleteProject,
  deletingId,
}: {
  projects: Project[];
  tickets: TicketWithProject[];
  activityFeed: ConsoleActivityItem[];
  agents: BureauAgentDef[];
  onProjectCreated: (p: Project) => void;
  onDeleteProject?: (p: Project) => void;
  deletingId?: string | null;
}) {
  const [filter, setFilter] = useState<"all" | ProjectStatus>("all");
  const [view, setView] = useState<"grid" | "list">("grid");
  const [createOpen, setCreateOpen] = useState(false);

  const counts = useMemo(() => {
    const byStatus: Record<string, number> = { all: projects.length };
    for (const p of projects) byStatus[p.status] = (byStatus[p.status] ?? 0) + 1;
    return byStatus;
  }, [projects]);

  const filtered = filter === "all" ? projects : projects.filter((p) => p.status === filter);

  const donutSegments = (["active", "beta", "dev", "paused"] as ProjectStatus[]).map((s) => ({
    color: PROJECT_COLOR[s],
    count: counts[s] ?? 0,
  }));

  const majThisWeek = tickets.filter((t) => inWindow(t.updated_at, 7, 0)).length;
  const activeProjects = counts.active ?? 0;

  return (
    <div className="flex min-h-0 flex-1 gap-3 overflow-y-auto">
      <div className="flex min-w-0 flex-1 flex-col gap-3">
        <div className="flex items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <span
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[10px] border text-[13px]"
              style={{
                borderColor: "rgba(192,138,114,.4)",
                background: "radial-gradient(circle at 30% 20%, rgba(192,138,114,.25), rgba(19,22,27,.9))",
                color: C.copperLight,
              }}
            >
              ▤
            </span>
            <div className="min-w-0">
              <h2 className="truncate text-[18px] font-bold tracking-[0.5px]" style={{ color: C.ivory }}>
                PROJETS
              </h2>
              <p className="truncate text-[10.5px]" style={{ color: C.dim }}>
                Vue d&apos;ensemble de tous les projets du département APP
              </p>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <span
              className="flex items-center gap-1.5 rounded-[16px] border px-3 py-1.5 text-[10.5px]"
              style={{ borderColor: "rgba(192,138,114,.22)", color: C.warm }}
            >
              <SlidersHorizontal className="h-3 w-3" /> Filtres
            </span>
            <span className="flex overflow-hidden rounded-lg border" style={{ borderColor: C.line }}>
              <button
                type="button"
                onClick={() => setView("grid")}
                className="flex h-[26px] w-[26px] items-center justify-center"
                style={{ background: view === "grid" ? "rgba(192,138,114,.18)" : "transparent", color: view === "grid" ? C.copperLight : C.faint }}
              >
                <LayoutGrid className="h-3.5 w-3.5" />
              </button>
              <button
                type="button"
                onClick={() => setView("list")}
                className="flex h-[26px] w-[26px] items-center justify-center"
                style={{ background: view === "list" ? "rgba(192,138,114,.18)" : "transparent", color: view === "list" ? C.copperLight : C.faint }}
              >
                <List className="h-3.5 w-3.5" />
              </button>
            </span>
            <span className="flex overflow-hidden rounded-[18px] border" style={{ borderColor: "rgba(192,138,114,.45)" }}>
              <button
                type="button"
                onClick={() => setCreateOpen(true)}
                className="flex items-center gap-1.5 px-3.5 py-1.5 text-[11px]"
                style={{ background: "rgba(192,138,114,.12)", color: C.copperLight }}
              >
                ＋ Nouveau projet
              </button>
              <Link
                href="/apps"
                className="flex items-center border-l px-3 py-1.5 text-[11px]"
                style={{ borderColor: "rgba(192,138,114,.3)", color: C.warm }}
                title="Lier un repo GitHub existant ou lancer une app via Factory"
              >
                Mes apps
              </Link>
            </span>
          </div>
        </div>

        <div className="flex gap-[22px] overflow-x-auto border-b" style={{ borderColor: "rgba(192,138,114,.15)" }}>
          {STATUS_FILTERS.map((f) => {
            const active = f.key === filter;
            return (
              <button
                key={f.key}
                type="button"
                onClick={() => setFilter(f.key)}
                className="flex shrink-0 items-center gap-1.5 whitespace-nowrap border-b-2 pb-2 pt-1 text-[11px]"
                style={{ borderColor: active ? C.copper : "transparent", color: active ? "#F5F2EA" : C.faint }}
              >
                {f.label}
                <span
                  className="rounded-full px-1.5 py-px text-[9px]"
                  style={{ background: "rgba(192,138,114,.12)", color: C.dim }}
                >
                  {counts[f.key] ?? 0}
                </span>
              </button>
            );
          })}
        </div>

        {filtered.length === 0 ? (
          <div
            className="flex min-h-[220px] flex-1 items-center justify-center rounded-xl px-6 text-center text-[11px]"
            style={{ border: `1px solid ${C.line}`, background: "rgba(19,22,27,.55)", color: C.faint }}
          >
            Aucun projet dans cette catégorie.
          </div>
        ) : view === "grid" ? (
          <div className="grid flex-1 auto-rows-min grid-cols-[repeat(auto-fill,minmax(250px,1fr))] gap-3 overflow-y-auto pb-1">
            {filtered.map((p) => (
              <ProjectCard key={p.id} project={p} tickets={tickets} agents={agents} />
            ))}
            <button
              type="button"
              onClick={() => setCreateOpen(true)}
              className="flex min-h-[220px] flex-col items-center justify-center gap-1.5 rounded-xl border border-dashed text-center"
              style={{ borderColor: "rgba(192,138,114,.25)" }}
            >
              <span
                className="flex h-9 w-9 items-center justify-center rounded-full text-[16px]"
                style={{ color: C.copperLight, border: `1px solid ${C.lineStrong}` }}
              >
                ＋
              </span>
              <span className="text-[11px] font-medium" style={{ color: C.warm }}>
                Nouveau projet
              </span>
              <span className="px-6 text-[9px]" style={{ color: C.faint }}>
                Créer un nouveau projet dans le département APP
              </span>
            </button>
          </div>
        ) : (
          <div className="flex flex-1 flex-col gap-1.5 overflow-y-auto pb-1">
            {filtered.map((p) => (
              <ProjectListRow
                key={p.id}
                project={p}
                tickets={tickets}
                onDelete={onDeleteProject}
                deleting={deletingId === p.id}
              />
            ))}
          </div>
        )}
      </div>

      <div className="hidden w-[clamp(240px,19vw,300px)] shrink-0 flex-col gap-3 min-[1200px]:flex">
        <div
          className="flex flex-col items-center gap-3 rounded-xl border p-3.5"
          style={{ borderColor: C.line, background: "rgba(19,22,27,.55)" }}
        >
          <p className="w-full text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
            RÉSUMÉ DES PROJETS
          </p>
          <DonutChart segments={donutSegments} />
          <div className="grid w-full grid-cols-2 gap-x-2 gap-y-1.5">
            {(["active", "beta", "dev", "paused"] as ProjectStatus[]).map((s) => (
              <span key={s} className="flex items-center gap-1.5 text-[9.5px]" style={{ color: C.warm }}>
                <span className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: PROJECT_COLOR[s] }} />
                {counts[s] ?? 0} {PROJECT_LABEL[s]}
              </span>
            ))}
          </div>
        </div>

        <div
          className="flex max-h-[300px] flex-col rounded-xl border p-3.5"
          style={{ borderColor: C.line, background: "rgba(19,22,27,.55)" }}
        >
          <div className="mb-2 flex items-center justify-between">
            <p className="text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
              ACTIVITÉ RÉCENTE GLOBALE
            </p>
            <Link href={ROUTES.activity} className="text-[9px]" style={{ color: C.copper }}>
              Tout voir
            </Link>
          </div>
          <div className="alnua-scroll flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto">
            {activityFeed.length === 0 ? (
              <p className="py-4 text-center text-[10px]" style={{ color: C.faint }}>
                Aucune activité récente.
              </p>
            ) : (
              activityFeed.slice(0, 8).map((ev) => (
                <div key={ev.id} className="flex items-start gap-2">
                  <span className="w-[30px] shrink-0 pt-px text-[8.5px]" style={{ color: C.faint }}>
                    {ev.time}
                  </span>
                  <span
                    className="mt-[3px] h-1.5 w-1.5 shrink-0 rounded-full"
                    style={{ background: (KIND_META[ev.kind] ?? KIND_META.create).color }}
                  />
                  <span className="min-w-0 flex-1">
                    <span className="block text-[10px] leading-[1.3]" style={{ color: C.warm }}>
                      <span style={{ color: C.ivory }}>{ev.agent}</span> {ev.action}
                    </span>
                    <span className="text-[8.5px]" style={{ color: C.faint }}>
                      {ev.dept}
                    </span>
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        <div
          className="grid grid-cols-2 gap-2 rounded-xl border p-3.5"
          style={{ borderColor: C.line, background: "rgba(19,22,27,.55)" }}
        >
          <p className="col-span-2 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
            MÉTRIQUES GLOBALES
          </p>
          {[
            { label: "Agents impliqués", value: agents.length },
            { label: "Tâches totales", value: tickets.length },
            { label: "MAJ cette semaine", value: majThisWeek },
            { label: "Projets actifs", value: activeProjects },
          ].map((m) => (
            <div
              key={m.label}
              className="rounded-[10px] border px-2.5 py-2"
              style={{ borderColor: C.lineSoft, background: "rgba(22,17,13,.5)" }}
            >
              <p className="text-[17px] font-semibold" style={{ color: C.ivory }}>
                {m.value}
              </p>
              <p className="text-[8px]" style={{ color: C.faint }}>
                {m.label}
              </p>
            </div>
          ))}
        </div>
      </div>

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
