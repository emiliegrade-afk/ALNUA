"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { toast } from "sonner";
import { AlnuaStar } from "@/components/brand/alnua-star";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { DeptV2PageShell } from "@/components/dept-v2";
import { AppConsole } from "@/components/app/app-console";
import { useConsoleData } from "@/components/console/console-provider";
import { ConsoleProvider } from "@/components/console/console-provider";
import { useAgentStatuses } from "@/hooks/use-agent-statuses";
import { getAgentsForBureau, type BureauAgentDef } from "@/lib/agent-bureau";
import { HUB_OWNER } from "@/lib/console/owner";
import { deleteProject, fetchProjects } from "@/lib/api";
import { ROUTES } from "@/lib/routes";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useBureauTickets } from "./tabs";
import { ProjetsTab } from "./projects-tab";
import { MissionsTab } from "./missions-tab";
import { BacklogTab } from "./backlog-tab";
import { DocumentationTab } from "./documentation-tab";
import { C, STATUS_LOAD, STATUS_TEXT, STATUS_COLOR, KIND_META, Ring, Bar, ALNUA_STAR_GLOW_RGB, ALNUA_STAR_SPARK_MID, ALNUA_STAR_SPARK_OUTER } from "./shared";
import { ApercuPanel, ChatPanel, MissionBox, RecentTasksPanel } from "./team";
import { CooDrawer } from "@/components/shared/coo-drawer";
import { useCooStore } from "@/store/coo-store";

/* ────────────────────────────────────────────────────────────────────────────
   Page de référence « APP Department » — portage fidèle de la maquette
   (projet Claude Design « Interface entreprise virtuelle », canevas 1536×1024).

   Isolée à dessein : elle ne consomme aucun composant de chrome partagé
   (ConsoleShell, BureauPage, DepartmentWorkspace…) et n'en modifie aucun. Elle
   rend son propre en-tête, sa propre sidebar et sa propre barre de commande,
   exactement comme le fichier source. Le reste du Hub ne peut donc pas être
   affecté par ce qui se passe ici.

   Adaptatif : les dimensions de la maquette sont reprises comme *maximum* dans
   des `clamp()` indexés sur la largeur de fenêtre, pour tenir sur un portable
   15" et s'étendre proprement au-delà. La hauteur n'est verrouillée qu'à
   partir de 660px de fenêtre — en dessous la page défile normalement plutôt
   que de couper le contenu.
   ──────────────────────────────────────────────────────────────────────────── */

const SUB_TABS: { label: string; icon: string }[] = [
  { label: "Équipe", icon: "👥" },
  { label: "Projets", icon: "▤" },
  { label: "Missions", icon: "◈" },
  { label: "Backlog", icon: "☰" },
  { label: "Documentation", icon: "📄" },
];

const QUICK_ACTIONS = [
  { icon: "＋", label: "Nouvelle mission" },
  { icon: "▤", label: "Rapport d'équipe" },
  { icon: "◎", label: "Analyse projet" },
  { icon: "⚙", label: "Automatisation" },
] as const;

function AppDepartmentView() {
  const agents = getAgentsForBureau("app");
  const statuses = useAgentStatuses();
  const { activityFeed, stats } = useConsoleData();
  const [selectedId, setSelectedId] = useState(agents[0]?.id ?? "");
  const [subTab, setSubTab] = useState<(typeof SUB_TABS)[number]["label"]>("Projets");
  const [projects, setProjects] = useState<Project[]>([]);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const { tickets, loading: ticketsLoading, setTickets } = useBureauTickets(projects);

  useEffect(() => {
    let cancelled = false;
    void fetchProjects()
      .then((all) => {
        if (!cancelled) setProjects(all.filter((p) => p.branch === "app"));
      })
      .catch(() => {
        if (!cancelled) setProjects([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleDeleteProject = useCallback(async (project: Project) => {
    if (
      !window.confirm(`Supprimer le projet « ${project.name} » ? Cette action est irréversible.`)
    ) {
      return;
    }
    setDeletingId(project.id);
    try {
      await deleteProject(project.id);
      toast.success(`Projet « ${project.name} » supprimé`);
      setProjects((prev) => prev.filter((p) => p.id !== project.id));
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Impossible de supprimer le projet");
    } finally {
      setDeletingId(null);
    }
  }, []);

  const openDrawer = useCooStore((s) => s.openDrawer);
  const setPrefillMessage = useCooStore((s) => s.setPrefillMessage);

  const selected: BureauAgentDef | undefined =
    agents.find((a) => a.id === selectedId) ?? agents[0];
  const selStatus = selected ? statuses[selected.id]?.status ?? "idle" : "idle";
  const selLoad = STATUS_LOAD[selStatus];

  /** Créer un agent passe par du code (checklist 6 étapes, CLAUDE.md), pas par
   * une UI — le bouton ouvre donc une vraie conversation avec Aria plutôt que
   * de mentir sur une action qui n'existe pas. */
  function requestNewAgent() {
    setPrefillMessage(
      "Je veux ajouter un agent au bureau App. Quel rôle manque-t-il et comment le créer ? ",
    );
    openDrawer();
  }
  const activeCount = agents.filter((a) => {
    const s = statuses[a.id]?.status;
    return s === "working" || s === "waiting";
  }).length;

  // Tâches récentes de l'agent sélectionné, tirées du flux réel.
  const agentTasks = useMemo(
    () => (selected ? activityFeed.filter((e) => e.agent === selected.name).slice(0, 6) : []),
    [activityFeed, selected],
  );

  if (!selected) {
    return (
      <p className="p-8 text-sm" style={{ color: C.dim }}>
        Aucun agent dans le bureau App.
      </p>
    );
  }

  return (
    <DeptV2PageShell deptHref={ROUTES.app} activeDeptId="app">
        <div className="flex min-w-0 flex-1 flex-col gap-3 px-4 pb-3 pt-3.5">
          {/* Rangée haute */}
          <div className="flex shrink-0 gap-3">
            <div className="flex min-w-0 flex-1 flex-col gap-2.5">
              {/* Titre + actions */}
              <div className="flex items-center justify-between gap-3">
                <div className="flex min-w-0 items-center gap-3">
                  <span
                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[10px] border text-[15px]"
                    style={{
                      borderColor: "rgba(192,138,114,.4)",
                      background:
                        "radial-gradient(circle at 30% 20%, rgba(192,138,114,.25), rgba(19,22,27,.9))",
                      color: C.copperLight,
                    }}
                  >
                    ◧
                  </span>
                  <div className="min-w-0">
                    <h1 className="truncate text-[23px] leading-[1.1] tracking-[1px]">
                      <span className="font-bold">APP</span>{" "}
                      <span className="font-light tracking-[4px]" style={{ color: "#A7ADB5" }}>
                        DEPARTMENT
                      </span>
                    </h1>
                    <p className="mt-0.5 truncate text-[11px]" style={{ color: C.dim }}>
                      Développement de nos produits digitaux
                    </p>
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-[9px]">
                  <span
                    className="hidden items-center gap-[7px] rounded-[18px] border px-[13px] py-1.5 text-[11.5px] sm:flex"
                    style={{
                      borderColor: "rgba(192,138,114,.22)",
                      background: "rgba(19,22,27,.6)",
                      color: C.warm,
                    }}
                  >
                    <span
                      className="h-1.5 w-1.5 rounded-full"
                      style={{ background: C.online, boxShadow: `0 0 6px ${C.online}` }}
                    />
                    {activeCount} agent{activeCount !== 1 ? "s" : ""} actif
                    {activeCount !== 1 ? "s" : ""}
                  </span>
                  <button
                    type="button"
                    onClick={requestNewAgent}
                    className="flex items-center gap-1.5 rounded-[18px] border px-[13px] py-1.5 text-[11.5px]"
                    style={{
                      borderColor: "rgba(192,138,114,.45)",
                      background: "rgba(192,138,114,.08)",
                      color: C.copperLight,
                    }}
                  >
                    ＋ <span className="hidden sm:inline">Ajouter un agent</span>
                  </button>
                  <span
                    className="flex h-[30px] w-[30px] items-center justify-center rounded-lg border"
                    style={{ borderColor: "rgba(192,138,114,.2)", color: C.dim }}
                  >
                    ⋮
                  </span>
                </div>
              </div>

              {/* Onglets */}
              <div
                className="flex gap-[22px] overflow-x-auto border-b"
                style={{ borderColor: "rgba(192,138,114,.15)" }}
              >
                {SUB_TABS.map((t) => {
                  const active = t.label === subTab;
                  return (
                    <button
                      key={t.label}
                      type="button"
                      onClick={() => setSubTab(t.label)}
                      className="flex shrink-0 items-center gap-[7px] whitespace-nowrap border-b-2 pb-2 pt-1 text-[10.5px] tracking-[1.2px]"
                      style={{
                        borderColor: active ? C.copper : "transparent",
                        color: active ? "#F5F2EA" : C.faint,
                      }}
                    >
                      <span className="text-[11px]">{t.icon}</span>
                      {t.label.toUpperCase()}
                    </button>
                  );
                })}
              </div>

              {/* Cartes agents — spécifique à l'onglet Équipe, absent du
                  tableau de bord Projets (et des autres onglets) dans la
                  maquette dédiée. */}
              {subTab === "Équipe" ? (
              <div className="flex h-[186px] gap-2.5">
                {agents.map((agent) => {
                  const s = statuses[agent.id]?.status ?? "idle";
                  const load = STATUS_LOAD[s];
                  const active = agent.id === selected.id;
                  return (
                    <button
                      key={agent.id}
                      type="button"
                      onClick={() => setSelectedId(agent.id)}
                      className="flex min-w-0 flex-1 basis-0 flex-col overflow-hidden rounded-xl border p-2.5 text-left transition-colors"
                      style={{
                        borderColor: active ? C.copper : C.line,
                        background: active
                          ? "radial-gradient(120% 120% at 0% 0%, rgba(192,138,114,.12), rgba(19,22,27,.6) 60%)"
                          : "rgba(19,22,27,.45)",
                        boxShadow: active ? "0 0 22px rgba(192,138,114,.12)" : undefined,
                      }}
                    >
                      <span className="flex items-center gap-2">
                        <AgentAvatar agentId={agent.id} name={agent.name} size={38} />
                        <span className="min-w-0 flex-1 leading-tight">
                          <span className="block truncate text-[12px] font-semibold">
                            {agent.name}
                          </span>
                          <span className="block truncate text-[9.5px]" style={{ color: C.dim }}>
                            {agent.role}
                          </span>
                          <span className="mt-[3px] flex items-center gap-1 text-[9px]">
                            <span
                              className="h-[5px] w-[5px] shrink-0 rounded-full"
                              style={{ background: STATUS_COLOR[s] }}
                            />
                            <span className="truncate" style={{ color: STATUS_COLOR[s] }}>
                              {STATUS_TEXT[s]}
                            </span>
                          </span>
                        </span>
                      </span>

                      <span
                        className="mt-2.5 block truncate text-[10px]"
                        style={{ color: C.warm }}
                      >
                        {statuses[agent.id]?.currentTask ?? "Aucune mission en cours"}
                      </span>

                      <span className="mt-1.5 flex items-center gap-1.5">
                        <Bar value={load} thick={2} />
                        <span className="relative h-[36px] w-[36px] shrink-0">
                          <Ring value={load} size={36} stroke={2.5} />
                          <span className="absolute inset-0 flex items-center justify-center text-[10px] font-semibold">
                            {load}%
                          </span>
                        </span>
                      </span>

                      <span className="mt-1.5 flex items-center gap-1.5">
                        <span className="shrink-0 text-[9.5px]" style={{ color: C.dim }}>
                          Charge
                        </span>
                        <Bar value={load} />
                        <span className="shrink-0 text-[9.5px]" style={{ color: "#A7ADB5" }}>
                          {load}%
                        </span>
                      </span>

                      {/* `overflow-hidden` sur le parent + `shrink-0` sur
                          chaque tag coupait le dernier tag en plein milieu
                          d'un caractère quand l'espace manquait (repéré dans
                          un panneau de prévisualisation anormalement étroit).
                          Chaque tag tronque désormais lui-même proprement
                          (`min-w-0` + `truncate`) au lieu d'être rogné par le
                          conteneur. */}
                      <span className="mt-auto flex min-w-0 gap-1 border-t pt-1.5" style={{ borderColor: "rgba(192,138,114,.12)" }}>
                        {agent.skills.slice(0, 3).map((sk) => (
                          <span
                            key={sk}
                            className="min-w-0 truncate rounded-[5px] border px-[5px] py-px text-[8.5px]"
                            style={{
                              borderColor: "rgba(192,138,114,.2)",
                              background: "rgba(192,138,114,.05)",
                              color: "#B5ABA1",
                            }}
                          >
                            {sk}
                          </span>
                        ))}
                      </span>
                    </button>
                  );
                })}

                <button
                  type="button"
                  onClick={requestNewAgent}
                  className="flex w-[92px] shrink-0 flex-col items-center justify-center gap-1.5 rounded-xl border border-dashed transition-colors hover:opacity-80"
                  style={{ borderColor: "rgba(192,138,114,.3)", background: "rgba(19,22,27,.3)" }}
                >
                  <span
                    className="flex h-[26px] w-[26px] items-center justify-center rounded-full border text-[14px]"
                    style={{ borderColor: "rgba(192,138,114,.35)", color: C.copperLight }}
                  >
                    ＋
                  </span>
                  <span className="text-center text-[9.5px] leading-[1.3]" style={{ color: C.dim }}>
                    Inviter
                    <br />
                    un agent
                  </span>
                </button>
              </div>
              ) : null}
            </div>

            {/* Activité temps réel — également spécifique à Équipe. */}
            {subTab === "Équipe" ? (
            <div
              className="flex h-[268px] w-[clamp(226px,18vw,276px)] shrink-0 flex-col rounded-xl border px-3 py-[11px]"
              style={{ borderColor: C.line, background: "rgba(19,22,27,.55)" }}
            >
              <div
                className="flex items-center justify-between border-b pb-[9px]"
                style={{ borderColor: C.lineSoft }}
              >
                <span className="text-[9.5px] tracking-[1.6px]" style={{ color: "#A7ADB5" }}>
                  ACTIVITÉ EN TEMPS RÉEL
                </span>
                <Link href={ROUTES.activity} className="text-[9.5px]" style={{ color: C.copper }}>
                  Tout voir
                </Link>
              </div>
              <div className="alnua-scroll flex min-h-0 flex-1 flex-col gap-[11px] overflow-y-auto py-2.5">
                {activityFeed.length === 0 ? (
                  <p className="py-6 text-center text-[10px]" style={{ color: C.faint }}>
                    Aucune activité récente.
                  </p>
                ) : (
                  activityFeed.slice(0, 12).map((ev) => (
                    <div key={ev.id} className="flex items-start gap-2">
                      <span
                        className="w-[29px] shrink-0 pt-[3px] text-[9.5px]"
                        style={{ color: C.faint }}
                      >
                        {ev.time}
                      </span>
                      <AgentAvatar agentId={ev.agent} name={ev.agent} size={24} />
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-[11px] font-semibold" style={{ color: "#E8DFD4" }}>
                          {ev.agent}
                        </span>
                        <span className="block text-[10px] leading-[1.35]" style={{ color: C.muted }}>
                          {ev.action}
                        </span>
                        <span className="mt-px block text-[9px]" style={{ color: C.faint }}>
                          {ev.dept}
                        </span>
                      </span>
                      <span
                        className="mt-[5px] h-1.5 w-1.5 shrink-0 rounded-full"
                        style={{ background: (KIND_META[ev.kind] ?? KIND_META.create).color }}
                      />
                    </div>
                  ))
                )}
              </div>
              <Link
                href={ROUTES.activity}
                className="rounded-lg border py-[7px] text-center text-[10.5px]"
                style={{ borderColor: "rgba(192,138,114,.22)", color: C.warm }}
              >
                Voir toute l&apos;activité
              </Link>
            </div>
            ) : null}
          </div>

          {/* ══ RANGÉE BASSE ══ */}
          {subTab !== "Équipe" ? (
            <div className="flex min-h-[clamp(340px,44vh,420px)] flex-1 flex-col">
              {subTab === "Projets" ? (
                <ProjetsTab
                  projects={projects}
                  tickets={tickets}
                  activityFeed={activityFeed}
                  agents={agents}
                  onProjectCreated={(p) => setProjects((prev) => [...prev, p])}
                  onDeleteProject={(p) => void handleDeleteProject(p)}
                  deletingId={deletingId}
                />
              ) : null}
              {subTab === "Missions" ? (
                <MissionsTab
                  tickets={tickets}
                  loading={ticketsLoading}
                  onChange={setTickets}
                  projects={projects}
                  agents={agents}
                  statuses={statuses}
                  activityFeed={activityFeed}
                />
              ) : null}
              {subTab === "Backlog" ? (
                <BacklogTab
                  tickets={tickets}
                  loading={ticketsLoading}
                  onChange={setTickets}
                  projects={projects}
                  agents={agents}
                  activityFeed={activityFeed}
                />
              ) : null}
              {subTab === "Documentation" ? <DocumentationTab projects={projects} /> : null}
            </div>
          ) : (
          <div className="flex min-h-[clamp(340px,44vh,420px)] flex-1 gap-3">
            {/* Roster — dimensionné à l'équipe réelle (5-6 agents ici), pas
                étiré pour égaler la hauteur du bloc Detail : `self-start`
                l'exclut du stretch par défaut de la rangée. Une équipe plus
                grande fait apparaître le défilement interne (max-h) plutôt
                que de repousser les cartes voisines. */}
            <div
              className="flex w-[clamp(176px,13.4vw,206px)] shrink-0 flex-col self-start rounded-xl border px-2.5 py-[11px]"
              style={{ borderColor: C.line, background: "rgba(19,22,27,.55)" }}
            >
              <div
                className="flex items-center justify-between border-b pb-[9px]"
                style={{ borderColor: C.lineSoft }}
              >
                <span className="text-[9.5px] tracking-[1.5px]" style={{ color: "#A7ADB5" }}>
                  ÉQUIPE APP
                </span>
                <span
                  className="flex items-center gap-1 rounded-[10px] border px-[6px] py-px text-[9px]"
                  style={{ borderColor: "rgba(140,200,150,.3)", color: C.onlineSoft }}
                >
                  <span className="h-[5px] w-[5px] rounded-full" style={{ background: C.online }} />
                  {activeCount > 0 ? "En ligne" : "En veille"} ▾
                </span>
              </div>
              <div className="alnua-scroll max-h-[240px] space-y-1 overflow-y-auto py-2">
                {agents.map((agent) => {
                  const s = statuses[agent.id]?.status ?? "idle";
                  const active = agent.id === selected.id;
                  return (
                    <button
                      key={agent.id}
                      type="button"
                      onClick={() => setSelectedId(agent.id)}
                      className="flex w-full items-center gap-2 rounded-lg px-1.5 py-1.5 text-left transition-colors"
                      style={
                        active
                          ? { background: "rgba(192,138,114,.12)" }
                          : undefined
                      }
                    >
                      <AgentAvatar agentId={agent.id} name={agent.name} size={32} />
                      <span className="min-w-0 flex-1">
                        <span
                          className="block truncate text-[11px] font-medium"
                          style={{ color: active ? C.copperLight : C.ivory }}
                        >
                          {agent.name}
                        </span>
                        <span className="block truncate text-[9px]" style={{ color: C.faint }}>
                          {agent.role}
                        </span>
                      </span>
                      <span className="flex shrink-0 flex-col items-end gap-[3px]">
                        <span className="text-[9.5px]" style={{ color: C.dim }}>
                          {STATUS_LOAD[s]}%
                        </span>
                        <span
                          className="h-[5px] w-[5px] rounded-full"
                          style={{ background: STATUS_COLOR[s] }}
                        />
                      </span>
                    </button>
                  );
                })}
              </div>
              <Link
                href={ROUTES.agents}
                className="rounded-lg border py-[6px] text-center text-[10px]"
                style={{ borderColor: "rgba(192,138,114,.22)", color: C.warm }}
              >
                Voir toute l&apos;équipe
              </Link>
            </div>

            {/* Detail */}
            <div
              className="flex min-w-0 flex-1 flex-col gap-[11px] rounded-xl border px-[13px] py-3"
              style={{
                borderColor: C.lineStrong,
                background:
                  "radial-gradient(120% 120% at 0% 0%, rgba(192,138,114,.08), rgba(19,22,27,.6) 55%)",
                boxShadow: "0 0 24px rgba(192,138,114,.07)",
              }}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex min-w-0 items-center gap-3">
                  <AgentAvatar agentId={selected.id} name={selected.name} size={56} ring />
                  <div className="min-w-0">
                    <div className="flex items-center gap-[7px]">
                      <span className="truncate text-[19px] font-semibold">{selected.name}</span>
                      <span className="text-[13px]" style={{ color: C.copperLight }}>
                        ✔
                      </span>
                    </div>
                    <p className="truncate text-[12px]" style={{ color: C.muted }}>
                      {selected.role}
                    </p>
                    <p className="mt-1 truncate text-[9.5px]" style={{ color: C.faint }}>
                      Spécialités : {selected.skills.join(" · ")}
                    </p>
                  </div>
                </div>
                <div className="flex shrink-0 flex-col items-end gap-1.5">
                  <div className="flex items-center gap-3.5 text-[10px]">
                    <span
                      className="flex items-center gap-1.5"
                      style={{ color: STATUS_COLOR[selStatus as keyof typeof STATUS_COLOR] }}
                    >
                      <span
                        className="h-[5px] w-[5px] rounded-full"
                        style={{ background: STATUS_COLOR[selStatus as keyof typeof STATUS_COLOR] }}
                      />
                      {STATUS_TEXT[selStatus as keyof typeof STATUS_TEXT]}
                    </span>
                    <Link
                      href={`${ROUTES.openroom}?agent=${encodeURIComponent(selected.id)}`}
                      className="rounded-[16px] border px-3 py-[5px] text-[10.5px]"
                      style={{ borderColor: C.lineStrong, color: "#E8DFD4" }}
                    >
                      Ouvrir le profil complet ↗
                    </Link>
                  </div>
                  <div className="flex gap-3.5 text-[10px]" style={{ color: C.dim }}>
                    <span>⊕ Bureau App</span>
                    <span>⏱ {selected.skills.length} compétences</span>
                  </div>
                </div>
              </div>

              <div className="flex min-h-0 flex-1 flex-col gap-[11px] min-[1240px]:flex-row">
                <MissionBox agent={selected} status={statuses[selected.id]} tickets={tickets} />
                <ChatPanel agent={selected} />
                <RecentTasksPanel tasks={agentTasks} />
              </div>
            </div>

            <ApercuPanel
              agent={selected}
              selLoad={selLoad}
              selStatus={selStatus}
              projects={projects}
              tickets={tickets}
              bureau="app"
            />
          </div>

          )}

          {/* ══ COMMAND BAR ══ */}
          <div className="relative flex h-[clamp(54px,7vh,62px)] shrink-0 items-center">
            <span
              className="absolute inset-0 rounded-[34px] border"
              style={{
                borderColor: "rgba(192,138,114,.28)",
                background:
                  "radial-gradient(60% 220% at 50% 50%, rgba(192,138,114,.14), rgba(14,11,9,.7) 70%)",
              }}
            />
            <div className="relative flex flex-1 items-center justify-between px-7">
              <span className="hidden text-[12px] sm:inline" style={{ color: C.muted }}>
                Que souhaitez-vous faire aujourd&apos;hui ?
              </span>
              <div className="ml-auto flex items-center gap-3 text-[11.5px]" style={{ color: C.warm }}>
                {QUICK_ACTIONS.map((qa) => (
                  <span key={qa.label} className="flex items-center gap-[7px]">
                    <span
                      className="flex h-[22px] w-[22px] items-center justify-center rounded-md border text-[10px]"
                      style={{ borderColor: "rgba(192,138,114,.28)", color: C.copperLight }}
                    >
                      {qa.icon}
                    </span>
                    <span className="hidden xl:inline">{qa.label}</span>
                  </span>
                ))}
              </div>
            </div>
            <span
              className="absolute left-1/2 top-1/2 flex h-[88px] w-[88px] -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full"
              style={{
                background:
                  "radial-gradient(circle, rgba(192,138,114,.30) 0%, rgba(192,138,114,.10) 45%, transparent 70%)",
              }}
            >
              <span
                className="absolute h-[76px] w-[76px] rounded-full border"
                style={{ borderColor: "rgba(192,138,114,.35)" }}
              />
              <AlnuaStar size={60} glow sparkMid={ALNUA_STAR_SPARK_MID} sparkOuter={ALNUA_STAR_SPARK_OUTER} glowColorRgb={ALNUA_STAR_GLOW_RGB} />
            </span>
          </div>

          {/* Console agents App — repliée par défaut, hors du canevas maquette
              (fonctionnalité réelle de l'ancienne /app, préservée mais pas
              visible sans défiler volontairement). */}
          <details className="group shrink-0 rounded-xl border" style={{ borderColor: C.line }}>
            <summary
              className="flex cursor-pointer items-center gap-2 px-4 py-2.5 text-[10.5px]"
              style={{ color: C.dim }}
            >
              <ChevronRight className="h-3.5 w-3.5 transition-transform group-open:rotate-90" />
              Console agents App — instructions directes
            </summary>
            <div
              className="alnua-scroll max-h-[46vh] overflow-y-auto border-t p-4"
              style={{ borderColor: C.line }}
            >
              <AppConsole />
            </div>
          </details>
        </div>
    </DeptV2PageShell>
  );
}

export default function AppDepartmentV2Page() {
  return (
    <ConsoleProvider>
      <AppDepartmentView />
      {/* Isolée du chrome partagé (voir en-tête du fichier), cette page rend
          son propre CooDrawer plutôt que de dépendre de celui monté par
          hub-shell.tsx — absent sur les routes "immersives" comme celle-ci. */}
      <CooDrawer />
    </ConsoleProvider>
  );
}
