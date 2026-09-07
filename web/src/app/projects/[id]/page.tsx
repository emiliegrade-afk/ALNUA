"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { AlnuaStar } from "@/components/brand/alnua-star";
import { ConsoleProvider, useConsoleData } from "@/components/console/console-provider";
import { useAgentStatuses } from "@/hooks/use-agent-statuses";
import { getAgentsForBureau, type BureauAgentDef, type BureauKey } from "@/lib/agent-bureau";
import { fetchProjects } from "@/lib/api";
import { fetchTicketsList, type TicketWithProject } from "@/lib/tickets";
import { fetchModules } from "@/lib/modules";
import { fetchRoadmapItems } from "@/lib/roadmap";
import { CreateRoadmapModal } from "@/components/roadmap/create-roadmap-modal";
import { PRIORITY_STYLES } from "@/components/roadmap/roadmap.constants";
import { ROUTES } from "@/lib/routes";
import type { Project, ProjectBranch, ProjectModule, RoadmapItem } from "@/lib/types";
import { C } from "../../app-v2/shared";
import { PROJECT_COLOR, PROJECT_LABEL, PROJECT_PROGRESS } from "../../app-v2/tabs";
import { backRouteFor } from "./project-nav";
import { TeamView } from "./team-view";
import { ModulesView } from "./modules-view";

/* Détail projet — données live (tickets, modules, roadmap) ; plus de phases /
 * insights / stats inventés (Vague D honesty). */

const TABS = ["Vue d'ensemble", "Modules", "Équipe", "Missions", "Roadmap", "Analytics", "Paramètres"] as const;
type Tab = (typeof TABS)[number];

/* La maquette montre un pipeline à 6 colonnes (Idées/Validation/Design/Dév/
   QA/Release) qui n'existe pas dans le modèle de tickets réel (4 statuts) —
   on garde les 4 vrais statuts plutôt que d'inventer 2 colonnes de plus. */
const MISSION_COLUMNS = [
  { status: "open", label: "IDÉES / BACKLOG" },
  { status: "in_progress", label: "DÉVELOPPEMENT" },
  { status: "in_review", label: "QA / REVIEW" },
  { status: "done", label: "RELEASE" },
] as const;

function branchToBureau(branch: ProjectBranch): BureauKey {
  if (branch === "gaming") return "gaming";
  if (branch === "robotics") return "robo";
  return "app";
}

function ProjectDetailView() {
  const params = useParams<{ id: string }>();
  const projectId = params.id;
  const [project, setProject] = useState<Project | null | undefined>(undefined);
  const [tickets, setTickets] = useState<TicketWithProject[]>([]);
  const [modules, setModules] = useState<ProjectModule[]>([]);
  const [modulesLoading, setModulesLoading] = useState(true);
  const [roadmapItems, setRoadmapItems] = useState<RoadmapItem[]>([]);
  const [createDecisionOpen, setCreateDecisionOpen] = useState(false);
  const [tab, setTab] = useState<Tab>("Vue d'ensemble");
  const statuses = useAgentStatuses();
  const { activityFeed } = useConsoleData();

  useEffect(() => {
    let cancelled = false;
    void fetchProjects().then((all) => {
      if (cancelled) return;
      setProject(all.find((p) => p.id === projectId) ?? null);
    });
    void fetchTicketsList({ project_id: projectId }).then((t) => {
      if (!cancelled) setTickets(t);
    });
    void fetchModules(projectId)
      .then((m) => {
        if (!cancelled) setModules(m);
      })
      .finally(() => {
        if (!cancelled) setModulesLoading(false);
      });
    void fetchRoadmapItems({ project_id: projectId }).then((r) => {
      if (!cancelled) setRoadmapItems(r);
    });
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  const agents = useMemo<BureauAgentDef[]>(
    () => (project ? getAgentsForBureau(branchToBureau(project.branch)) : []),
    [project],
  );

  if (project === undefined) {
    return (
      <div className="flex h-full w-full items-center justify-center" style={{ background: "#08090B", color: C.faint }}>
        Chargement…
      </div>
    );
  }
  if (project === null) {
    return (
      <div
        className="flex h-full w-full flex-col items-center justify-center gap-3"
        style={{ background: "#08090B", color: C.faint }}
      >
        <p>Projet introuvable.</p>
        <Link href={ROUTES.app} className="underline" style={{ color: C.copperLight }}>
          ← Retour aux projets
        </Link>
      </div>
    );
  }

  const decisions = roadmapItems.filter((r) => r.status === "idea" || r.status === "planned");
  const totalFeatures = modules.reduce((s, m) => s + m.features_total, 0);
  const featuresDone = modules.reduce((s, m) => s + m.features_done, 0);
  const openBugs = modules.reduce((s, m) => s + m.open_bugs, 0);
  const globalProgress = PROJECT_PROGRESS[project.status];
  const openTickets = tickets.filter((t) => t.status === "open" || t.status === "in_progress").length;
  const insightParts = [
    modules.length > 0
      ? `${modules.length} module${modules.length > 1 ? "s" : ""} · ${featuresDone}/${totalFeatures || "—"} features`
      : "Aucun module encore",
    openTickets > 0 ? `${openTickets} ticket${openTickets > 1 ? "s" : ""} actif${openTickets > 1 ? "s" : ""}` : "Aucun ticket actif",
    openBugs > 0 ? `${openBugs} bug${openBugs > 1 ? "s" : ""} ouvert${openBugs > 1 ? "s" : ""}` : null,
    decisions.length > 0 ? `${decisions.length} décision${decisions.length > 1 ? "s" : ""} en attente` : null,
  ].filter(Boolean);

  return (
    <div
      className="alnua-scroll flex h-full w-full flex-col overflow-y-auto"
      style={{
        background:
          "radial-gradient(900px 500px at 12% -5%, rgba(200,127,78,.10), transparent 60%), #08090B",
        color: C.ivory,
      }}
    >
      {/* ══ HEADER ══ */}
      <header className="flex flex-col gap-4 border-b px-6 py-4" style={{ borderColor: C.line }}>
        <div className="flex items-center gap-3">
          <Link
            href={backRouteFor(project.branch)}
            className="flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-[11px]"
            style={{ borderColor: C.line, color: C.warm }}
          >
            ← Retour
          </Link>
          <span className="h-4 w-px" style={{ background: C.line }} />
          <AlnuaStar size={22} animated={false} sparkMid="#E8A87C" sparkOuter="#C87F4E" glowColorRgb="200,127,78" />
        </div>

        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <h1 className="truncate text-[26px] font-bold tracking-[1px]" style={{ color: C.ivory }}>
              {project.name}
            </h1>
            <p className="mt-1 truncate text-[12px]" style={{ color: C.muted }}>
              {project.description || "—"}
            </p>
            <div className="mt-2.5 flex items-center gap-2">
              <span
                className="rounded-full border px-2.5 py-0.5 text-[10px]"
                style={{ borderColor: "rgba(200,127,78,.3)", color: PROJECT_COLOR[project.status] }}
              >
                {PROJECT_LABEL[project.status]}
              </span>
              <span
                className="rounded-full border px-2.5 py-0.5 text-[10px]"
                style={{ borderColor: "rgba(200,127,78,.3)", color: C.warm }}
              >
                Créé {new Date(project.created_at).toLocaleDateString("fr-FR")}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="relative h-[64px] w-[64px] shrink-0">
              <svg width="64" height="64" viewBox="0 0 64 64">
                <circle cx="32" cy="32" r="27" fill="none" stroke="rgba(200,127,78,.15)" strokeWidth="5" />
                <circle
                  cx="32"
                  cy="32"
                  r="27"
                  fill="none"
                  stroke={C.copper}
                  strokeWidth="5"
                  strokeLinecap="round"
                  strokeDasharray={`${((globalProgress / 100) * 2 * Math.PI * 27).toFixed(1)} ${(2 * Math.PI * 27).toFixed(1)}`}
                  transform="rotate(-90 32 32)"
                />
              </svg>
              <span className="absolute inset-0 flex items-center justify-center text-[15px] font-semibold">
                {globalProgress}%
              </span>
            </div>
            <div className="text-[10.5px]" style={{ color: C.faint }}>
              <p style={{ color: C.warm }}>Progression (statut)</p>
              <p>
                {totalFeatures > 0
                  ? `${featuresDone}/${totalFeatures} fonctionnalités`
                  : "Pas de features module"}
              </p>
            </div>
            <div
              className="flex flex-col gap-0.5 rounded-lg border px-3 py-2 text-[10px]"
              style={{ borderColor: C.line, color: C.faint }}
            >
              <span style={{ color: C.warm }}>Bugs ouverts</span>
              <span>{modules.length > 0 ? openBugs : "—"}</span>
            </div>
          </div>
        </div>

        <div className="flex gap-5 overflow-x-auto border-t pt-3" style={{ borderColor: C.lineSoft }}>
          {TABS.map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setTab(t)}
              className="shrink-0 whitespace-nowrap border-b-2 pb-2 text-[11px] tracking-[0.5px]"
              style={{ borderColor: tab === t ? C.copper : "transparent", color: tab === t ? "#F2E9DE" : C.faint }}
            >
              {t.toUpperCase()}
            </button>
          ))}
        </div>
      </header>

      {/* ══ CONTENU ══ */}
      <div className="flex-1 p-6">
        {tab === "Vue d'ensemble" ? (
          <div className="flex flex-col gap-4">
            <section
              className="rounded-xl border p-4"
              style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}
            >
              <p className="mb-3 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
                MODULES — SANTÉ
              </p>
              {modules.length === 0 ? (
                <p className="py-3 text-center text-[10px]" style={{ color: C.faint }}>
                  Aucun module — crée-en dans l&apos;onglet Modules. Pas de pipeline
                  de phases inventé.
                </p>
              ) : (
                <div className="flex flex-wrap gap-4">
                  {modules.slice(0, 6).map((m) => (
                    <div
                      key={m.id}
                      className="flex flex-1 flex-col items-center gap-1.5"
                      style={{ minWidth: 90 }}
                    >
                      <div className="relative h-[46px] w-[46px]">
                        <svg width="46" height="46" viewBox="0 0 46 46">
                          <circle
                            cx="23"
                            cy="23"
                            r="19"
                            fill="none"
                            stroke="rgba(200,127,78,.15)"
                            strokeWidth="4"
                          />
                          <circle
                            cx="23"
                            cy="23"
                            r="19"
                            fill="none"
                            stroke={m.progress === 100 ? C.online : C.copper}
                            strokeWidth="4"
                            strokeLinecap="round"
                            strokeDasharray={`${((m.progress / 100) * 2 * Math.PI * 19).toFixed(1)} ${(2 * Math.PI * 19).toFixed(1)}`}
                            transform="rotate(-90 23 23)"
                          />
                        </svg>
                        <span className="absolute inset-0 flex items-center justify-center text-[10px] font-semibold">
                          {m.progress}%
                        </span>
                      </div>
                      <span className="line-clamp-2 text-center text-[10px]" style={{ color: C.warm }}>
                        {m.name}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <div className="grid gap-4 lg:grid-cols-[1.3fr_1fr]">
              <div className="flex flex-col gap-4">
                <section
                  className="rounded-xl border p-4"
                  style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}
                >
                  <p className="mb-3 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
                    PIPELINE DES MISSIONS
                  </p>
                  <div className="grid grid-cols-4 gap-2">
                    {MISSION_COLUMNS.map((col) => {
                      const colTickets = tickets.filter((t) => t.status === col.status);
                      return (
                        <div
                          key={col.status}
                          className="flex flex-col gap-1.5 rounded-lg border p-2"
                          style={{ borderColor: C.lineSoft, background: "rgba(22,17,13,.4)" }}
                        >
                          <span className="text-[8.5px] tracking-[0.5px]" style={{ color: C.faint }}>
                            {col.label}
                          </span>
                          <span className="text-[18px] font-semibold" style={{ color: C.ivory }}>
                            {colTickets.length}
                          </span>
                          {colTickets[0] ? (
                            <span className="truncate text-[8.5px]" style={{ color: C.dim }}>
                              {colTickets[0].title}
                            </span>
                          ) : null}
                        </div>
                      );
                    })}
                  </div>
                </section>

                <section
                  className="rounded-xl border p-4"
                  style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}
                >
                  <p className="mb-3 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
                    ÉQUIPE DU PROJET
                  </p>
                  <div className="flex flex-col gap-2">
                    {agents.slice(0, 5).map((a) => {
                      const s = statuses[a.id]?.status ?? "idle";
                      return (
                        <div key={a.id} className="flex items-center gap-2.5">
                          <span className="min-w-0 flex-1 truncate text-[11.5px] font-medium">{a.name}</span>
                          <span className="w-[110px] shrink-0 truncate text-[9.5px]" style={{ color: C.faint }}>
                            {a.role}
                          </span>
                          <span
                            className="w-[70px] shrink-0 text-[9px]"
                            style={{ color: s === "working" || s === "waiting" ? C.online : C.faint }}
                          >
                            {s === "working" || s === "waiting" ? "En activité" : "En veille"}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </section>

                <section
                  className="rounded-xl border p-4"
                  style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}
                >
                  <p className="mb-3 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
                    ACTIVITÉ RÉCENTE
                  </p>
                  {activityFeed.length === 0 ? (
                    <p className="py-3 text-center text-[10px]" style={{ color: C.faint }}>
                      Aucune activité récente.
                    </p>
                  ) : (
                    <div className="flex flex-col gap-2">
                      {activityFeed.slice(0, 5).map((ev) => (
                        <div key={ev.id} className="flex items-center gap-2 text-[10.5px]">
                          <span className="w-[32px] shrink-0" style={{ color: C.faint }}>
                            {ev.time}
                          </span>
                          <span style={{ color: C.ivory }}>{ev.agent}</span>
                          <span className="min-w-0 flex-1 truncate" style={{ color: C.muted }}>
                            {ev.action}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </section>
              </div>

              <div className="flex flex-col gap-4">
                <section
                  className="rounded-xl border p-4"
                  style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}
                >
                  <div className="mb-3 flex items-center justify-between">
                    <p className="text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
                      DÉCISIONS EN ATTENTE
                    </p>
                    <button
                      type="button"
                      onClick={() => setCreateDecisionOpen(true)}
                      className="text-[9.5px]"
                      style={{ color: C.copperLight }}
                    >
                      ＋ Ajouter
                    </button>
                  </div>
                  <div className="flex flex-col gap-2">
                    {decisions.length === 0 ? (
                      <p className="py-3 text-center text-[10px]" style={{ color: C.faint }}>
                        Aucune décision en attente — les idées/planifiés de la roadmap apparaissent ici.
                      </p>
                    ) : (
                      decisions.map((d) => (
                        <div
                          key={d.id}
                          className="flex items-center justify-between gap-2 rounded-lg border px-3 py-2"
                          style={{ borderColor: C.lineSoft }}
                        >
                          <span className="min-w-0 flex-1">
                            <span className="block text-[11px] font-medium" style={{ color: C.ivory }}>
                              {d.title}
                            </span>
                            <span className="block truncate text-[9.5px]" style={{ color: C.faint }}>
                              {d.description || "—"}
                            </span>
                          </span>
                          <span
                            className="shrink-0 text-[9px] uppercase"
                            style={{ color: d.priority === "critical" || d.priority === "high" ? "#f87171" : C.faint }}
                          >
                            {PRIORITY_STYLES[d.priority].label}
                          </span>
                        </div>
                      ))
                    )}
                  </div>
                </section>

                <section
                  className="rounded-xl border p-4"
                  style={{ borderColor: "rgba(200,127,78,.3)", background: "rgba(22,17,13,.5)" }}
                >
                  <p className="mb-2 text-[9.5px] tracking-[1.5px]" style={{ color: C.copperLight }}>
                    SYNTHÈSE LIVE
                  </p>
                  <p className="text-[11px] leading-relaxed" style={{ color: C.warm }}>
                    {insightParts.join(" · ")}.
                  </p>
                </section>
              </div>
            </div>
          </div>
        ) : null}

        {tab === "Modules" ? (
          <ModulesView
            project={project}
            modules={modules}
            loading={modulesLoading}
            onModulesChange={setModules}
          />
        ) : null}

        {tab === "Équipe" ? <TeamView project={project} agents={agents} statuses={statuses} /> : null}

        {tab === "Missions" ? (
          <section
            className="rounded-xl border p-4"
            style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}
          >
            <p className="mb-3 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
              TICKETS DU PROJET
            </p>
            {tickets.length === 0 ? (
              <p className="py-6 text-center text-[11px]" style={{ color: C.faint }}>
                Aucun ticket pour ce projet.
              </p>
            ) : (
              <div className="flex flex-col gap-1.5">
                {tickets.map((t) => (
                  <div
                    key={t.id}
                    className="flex items-center gap-2 rounded-lg border px-3 py-2 text-[11px]"
                    style={{ borderColor: C.lineSoft }}
                  >
                    <span className="min-w-0 flex-1 truncate">{t.title}</span>
                    <span style={{ color: C.faint }}>{t.status}</span>
                  </div>
                ))}
              </div>
            )}
          </section>
        ) : null}

        {tab === "Roadmap" || tab === "Analytics" || tab === "Paramètres" ? (
          <div
            className="flex min-h-[240px] items-center justify-center rounded-xl border text-[11px]"
            style={{ borderColor: C.line, background: "rgba(16,13,11,.55)", color: C.faint }}
          >
            {tab} — à venir.
          </div>
        ) : null}
      </div>

      <CreateRoadmapModal
        open={createDecisionOpen}
        onOpenChange={setCreateDecisionOpen}
        projects={[project]}
        defaultProjectId={project.id}
        defaultStatus="idea"
        onCreated={(item) => setRoadmapItems((prev) => [...prev, item])}
      />
    </div>
  );
}

export default function ProjectDetailPage() {
  return (
    <ConsoleProvider>
      <ProjectDetailView />
    </ConsoleProvider>
  );
}
