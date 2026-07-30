"use client";

import Link from "next/link";
import { ArrowRight, Loader2, Trash2 } from "lucide-react";
import { Bars, Donut, LevelBar } from "@/components/console/charts";
import { Button } from "@/components/ui/button";
import type { TicketWithProject } from "@/lib/tickets";
import { ROUTES } from "@/lib/routes";
import type { DeptKey } from "@/lib/dept-colors";
import type { Project, ProjectBranch, ProjectStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const STATUS_DONUT_COLOR: Record<ProjectStatus, string> = {
  active: "#34d399",
  beta: "#C08A72",
  dev: "#60a5fa",
  paused: "#71717a",
};

interface ProjectGridProps {
  dept: DeptKey;
  projects: Project[];
  loading: boolean;
  /** Tickets du bureau — sert à afficher la charge réelle par projet. Les
   * maquettes montrent une équipe et une stack sur chaque carte ; le modèle
   * `Project` ne porte ni l'une ni l'autre, donc on affiche la charge, qui
   * est une donnée réelle, plutôt qu'une équipe devinée. */
  tickets?: TicketWithProject[];
  /** Only App's project registry supports delete today — optional so other
   * bureaus don't get a delete affordance they never had. */
  onDelete?: (project: Project) => void;
  deletingId?: string | null;
}

/** Only 3 of 9 operational bureaus have a real project concept today —
 * everything else gets an honest, bureau-specific empty state rather than a
 * guessed "project" model nobody validated (TASTE DECISION #3). */
const DEPT_TO_BRANCH: Partial<Record<DeptKey, ProjectBranch>> = {
  app: "app",
  gaming: "gaming",
  robo: "robotics",
};

const EMPTY_STATE_COPY: Partial<Record<DeptKey, string>> = {
  marketing: "Le suivi de campagnes n'est pas encore modélisé comme projet ici.",
  finances: "Le suivi budgétaire n'est pas encore modélisé comme projet ici.",
  rd: "Les dossiers R&D ne sont pas encore modélisés comme projets ici.",
  analytics: "Les analyses ne sont pas encore modélisées comme projets ici.",
  secretary: "La coordination du secrétariat ne passe pas encore par des projets.",
  hub: "La direction ne suit pas encore son activité sous forme de projets.",
  ceo: "Le pilotage exécutif ne passe pas encore par des projets.",
};

/** Heuristic status→progress mapping (frontend `ProjectStatus`, not the
 * backend's `_branch_progress` on `status: str` — different vocabulary,
 * see PLAN_DEPARTMENTS_UI_REDESIGN.md "GATE HUMAIN" for why). Always
 * returns a number — this bureau's projects never have an "unavailable"
 * progress the way the review anticipated, only a real percentage. */
const STATUS_PROGRESS: Record<ProjectStatus, number> = {
  paused: 20,
  dev: 45,
  beta: 80,
  active: 100,
};

const STATUS_LABEL: Record<ProjectStatus, string> = {
  paused: "En pause",
  dev: "En dev",
  beta: "Bêta",
  active: "Actif",
};

export function ProjectGrid({
  dept,
  projects,
  loading,
  tickets = [],
  onDelete,
  deletingId,
}: ProjectGridProps) {
  const branch = DEPT_TO_BRANCH[dept];

  if (!branch) {
    return (
      <div className="rounded-xl border border-bronze-faint bg-obsidian/50 px-6 py-10 text-center">
        <p className="text-sm text-titane/70">
          Ce bureau ne suit pas encore de projets structurés.
        </p>
        <p className="mt-1 text-xs text-titane/45">
          {EMPTY_STATE_COPY[dept] ?? "Aucun concept de projet n'est encore défini pour ce bureau."}
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[0, 1, 2].map((i) => (
          <div key={i} className="h-40 animate-pulse rounded-xl border border-bronze-faint bg-obsidian/50" />
        ))}
      </div>
    );
  }

  if (projects.length === 0) {
    return (
      <div className="rounded-xl border border-bronze-faint bg-obsidian/50 px-6 py-10 text-center">
        <p className="text-sm text-titane/70">Aucun projet pour le moment.</p>
      </div>
    );
  }

  const statusCounts = (["active", "beta", "dev", "paused"] as ProjectStatus[])
    .map((s) => ({ status: s, count: projects.filter((p) => p.status === s).length }))
    .filter((s) => s.count > 0);
  const typeCounts = Object.entries(
    projects.reduce<Record<string, number>>((acc, p) => {
      acc[p.branch] = (acc[p.branch] ?? 0) + 1;
      return acc;
    }, {})
  ).map(([label, value]) => ({ label, value }));

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_260px]">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {projects.map((project) => {
        const progress = STATUS_PROGRESS[project.status];
        const projectTickets = tickets.filter((t) => t.project_id === project.id);
        const openCount = projectTickets.filter(
          (t) => t.status === "open" || t.status === "in_progress" || t.status === "in_review"
        ).length;
        const criticalCount = projectTickets.filter(
          (t) => t.priority === "critical" && t.status !== "done" && t.status !== "wont_fix"
        ).length;
        return (
          <div
            key={project.id}
            className="group relative flex flex-col overflow-hidden rounded-xl border border-bronze-faint bg-obsidian/70 p-4 transition-colors hover:border-bronze/40"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <span
                  className={cn(
                    "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-medium uppercase tracking-wide",
                    project.status === "active" && "border-emerald-500/25 bg-emerald-500/10 text-emerald-300",
                    project.status === "beta" && "border-copper/30 bg-copper/10 text-copper-glow",
                    project.status === "dev" && "border-blue-500/25 bg-blue-500/10 text-blue-300",
                    project.status === "paused" && "border-zinc-500/25 bg-zinc-500/10 text-zinc-400"
                  )}
                >
                  <span
                    className={cn(
                      "h-1.5 w-1.5 rounded-full",
                      project.status === "active" && "bg-emerald-400",
                      project.status === "beta" && "bg-copper-glow",
                      project.status === "dev" && "bg-blue-400",
                      project.status === "paused" && "bg-zinc-400"
                    )}
                  />
                  {STATUS_LABEL[project.status]}
                </span>
                <h3 className="mt-2.5 truncate font-title text-base font-semibold uppercase tracking-wide text-ivoire">
                  {project.name}
                </h3>
              </div>
              <Donut
                segments={[
                  { value: progress, color: "#C08A72" },
                  { value: 100 - progress, color: "#1C2027" },
                ]}
                size={64}
                thickness={7}
                centerValue={`${progress}%`}
                className="shrink-0"
              />
            </div>

            <p className="mt-2 line-clamp-2 min-h-[2rem] text-xs text-titane/60">
              {project.description}
            </p>

            <div className="mt-3">
              <div className="mb-1 flex items-center justify-between text-[10px] uppercase tracking-wide text-titane/45">
                <span>Avancement</span>
                <span className="tabular-nums">{progress}%</span>
              </div>
              <LevelBar value={progress} />
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-1.5 border-t border-bronze-faint pt-3">
              <span className="rounded border border-bronze-faint bg-obsidian-deep/60 px-1.5 py-0.5 text-[9px] uppercase tracking-wide text-titane/55">
                {project.branch}
              </span>
              <span
                className={cn(
                  "rounded border px-1.5 py-0.5 text-[9px]",
                  openCount > 0
                    ? "border-copper/25 bg-copper/10 text-copper-glow"
                    : "border-bronze-faint bg-obsidian-deep/60 text-titane/50"
                )}
              >
                {openCount} mission{openCount !== 1 ? "s" : ""} en cours
              </span>
              {criticalCount > 0 ? (
                <span className="rounded border border-red-500/30 bg-red-500/10 px-1.5 py-0.5 text-[9px] text-red-300">
                  {criticalCount} critique{criticalCount !== 1 ? "s" : ""}
                </span>
              ) : null}
            </div>

            <div className="mt-3 flex items-center gap-2">
              <Link
                href={`${ROUTES.tickets}?project=${encodeURIComponent(project.id)}`}
                className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-bronze-faint bg-obsidian-deep/60 px-3 py-2 text-xs font-medium text-titane/75 transition-colors hover:border-bronze/40 hover:text-bronze-bright"
              >
                Voir le projet
                <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
              </Link>
              {onDelete ? (
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={deletingId === project.id}
                  onClick={() => onDelete(project)}
                  aria-label={`Supprimer ${project.name}`}
                  className="h-9 w-9 shrink-0 p-0 text-titane/60 hover:text-red-400"
                >
                  {deletingId === project.id ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Trash2 className="h-4 w-4" />
                  )}
                </Button>
              ) : null}
            </div>
          </div>
        );
        })}
      </div>

      <div className="space-y-4">
        <div className="rounded-xl border border-bronze-faint bg-obsidian/70 p-4">
          <p className="label-caps mb-3">Répartition par statut</p>
          <div className="flex items-center gap-4">
            <Donut
              segments={statusCounts.map((s) => ({
                value: s.count,
                color: STATUS_DONUT_COLOR[s.status],
              }))}
              size={96}
              thickness={12}
              centerValue={String(projects.length)}
              centerLabel="projets"
            />
            <ul className="space-y-1.5 text-xs">
              {statusCounts.map((s) => (
                <li key={s.status} className="flex items-center gap-2">
                  <span
                    className="h-2 w-2 rounded-full"
                    style={{ background: STATUS_DONUT_COLOR[s.status] }}
                  />
                  <span className="text-titane/70">{STATUS_LABEL[s.status]}</span>
                  <span className="ml-auto text-ivoire/80">{s.count}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="rounded-xl border border-bronze-faint bg-obsidian/70 p-4">
          <p className="label-caps mb-3">Répartition par branche</p>
          <Bars data={typeCounts} height={120} color="#C08A72" />
        </div>
      </div>
    </div>
  );
}
