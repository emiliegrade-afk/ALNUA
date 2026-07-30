"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { toast } from "sonner";
import { AlnuaStar } from "@/components/brand/alnua-star";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { AppConsole } from "@/components/app/app-console";
import { useConsoleData } from "@/components/console/console-provider";
import { ConsoleProvider } from "@/components/console/console-provider";
import { useAgentStatuses } from "@/hooks/use-agent-statuses";
import { getAgentsForBureau, type BureauAgentDef } from "@/lib/agent-bureau";
import { CONSOLE_POLES } from "@/lib/console/departments";
import { HUB_CHIEF, HUB_OWNER } from "@/lib/console/owner";
import { deleteProject, fetchProjects } from "@/lib/api";
import { ROUTES } from "@/lib/routes";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useBureauTickets } from "./tabs";
import { ProjetsTab } from "./projects-tab";
import { MissionsTab } from "./missions-tab";
import { BacklogTab } from "./backlog-tab";
import { DocumentationTab } from "./documentation-tab";
import { C, STATUS_LOAD, STATUS_TEXT, STATUS_COLOR, KIND_META, Ring, Bar } from "./shared";
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

// Icônes et libellés repris à l'identique du fichier source de la maquette
// (grep direct sur app-dept.html — plus de reconstruction approximative).
const DASHBOARD_NAV: { icon: string; label: string; href: string; badge?: boolean }[] = [
  { icon: "◉", label: "Command Center", href: ROUTES.home },
  { icon: "〰", label: "Activité en direct", href: ROUTES.activity },
  { icon: "▤", label: "Décisions", href: ROUTES.ceo, badge: true },
];

/** "Modèles"/"Automatisations" n'ont pas de page dédiée dans le Hub (réglages
 * modèles → Paramètres, automatisations → n8n externe, pas de route Hub) —
 * les deux pointent donc vers /settings plutôt qu'un lien mort inventé. */
const TOOLS_NAV = [
  { icon: "📄", label: "Documents", href: "/docs" },
  { icon: "📖", label: "Connaissances", href: ROUTES.library },
  { icon: "🗒", label: "Modèles", href: ROUTES.settings },
  { icon: "⚙", label: "Automatisations", href: ROUTES.settings },
] as const;

const TOP_TABS: { icon: string; label: string; href: string; active?: boolean }[] = [
  { icon: "☰", label: "Vue générale", href: ROUTES.home },
  { icon: "▦", label: "Départements", href: ROUTES.app, active: true },
  { icon: "◈", label: "Missions", href: ROUTES.tickets },
  { icon: "📈", label: "Analytics", href: ROUTES.analytics },
  { icon: "🗂", label: "Ressources", href: ROUTES.library },
];

/** Icônes par pôle — reprises à l'identique de la maquette (grep app-dept.html). */
const DEPT_ICON: Record<string, string> = {
  hub: "◎",
  secretary: "🗂",
  rd: "◇",
  app: "▦",
  marketing: "📣",
  gaming: "🎮",
  robo: "🤖",
  finances: "💠",
  analytics: "📈",
  brand: "🎨",
};

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

function SectionBox({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div
      className="rounded-[10px] border p-2"
      style={{ borderColor: "rgba(200,127,78,.14)", background: "rgba(16,13,11,.5)" }}
    >
      <p
        className="mb-2 ml-2 mt-0.5 text-[8.5px] tracking-[0.2em]"
        style={{ color: C.faint }}
      >
        {title}
      </p>
      {children}
    </div>
  );
}

function AppDepartmentView() {
  const agents = getAgentsForBureau("app");
  const statuses = useAgentStatuses();
  const { activityFeed, stats } = useConsoleData();
  const [selectedId, setSelectedId] = useState(agents[0]?.id ?? "");
  const [subTab, setSubTab] = useState<(typeof SUB_TABS)[number]["label"]>("Équipe");
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
    <div
      // Le shell rend cette route dans un conteneur `fixed inset-0
      // overflow-hidden` : c'est donc ICI que doit vivre le défilement, sinon
      // le bas de la page est coupé sans aucun moyen d'y accéder. Aucune
      // hauteur n'est verrouillée — la maquette fait 1024px de haut, un
      // portable 15" en offre souvent moins.
      className="alnua-scroll flex h-full w-full flex-col overflow-x-auto overflow-y-auto"
      style={{
        background:
          "radial-gradient(900px 500px at 12% -5%, rgba(200,127,78,.10), transparent 60%), radial-gradient(1000px 600px at 88% 105%, rgba(200,127,78,.09), transparent 62%), #08090B",
        color: C.ivory,
      }}
    >
      {/* ══ HEADER ══ */}
      <header
        className="flex h-[clamp(56px,6vh,64px)] shrink-0 items-stretch border-b"
        style={{ borderColor: C.line }}
      >
        <Link
          href={ROUTES.home}
          className="flex w-[clamp(178px,13.7vw,210px)] shrink-0 items-center gap-[11px] border-r pl-[18px]"
          style={{ borderColor: C.line }}
        >
          <span
            className="flex h-[38px] w-[38px] shrink-0 items-center justify-center rounded-full border"
            style={{
              borderColor: "rgba(200,127,78,.45)",
              background: "radial-gradient(circle,rgba(200,127,78,.28),transparent 70%)",
              boxShadow: "0 0 18px rgba(200,127,78,.25)",
            }}
          >
            <AlnuaStar size={24} animated={false} sparkMid="#E8A87C" sparkOuter="#C87F4E" glowColorRgb="200,127,78" />
          </span>
          <span>
            <span
              className="block font-title text-[21px] leading-none tracking-[4px]"
              style={{ color: C.copperLight }}
            >
              ALNUA
            </span>
            <span
              className="mt-[3px] block text-[8px] tracking-[3.4px]"
              style={{ color: C.dim }}
            >
              AGENTIC OS
            </span>
          </span>
        </Link>

        <div className="flex flex-1 items-center justify-between gap-4 px-5">
          <div className="flex min-w-0 items-center gap-[11px]">
            <AgentAvatar agentId={HUB_CHIEF.agentId} name={HUB_CHIEF.name} size={38} ring />
            <span className="min-w-0">
              <span className="block truncate text-[12.5px] font-medium">
                {HUB_CHIEF.shortRole} : {HUB_CHIEF.name}
              </span>
              <span className="mt-[3px] flex items-center gap-2">
                <span
                  className="flex items-center gap-1 rounded-[10px] border px-[7px] py-px"
                  style={{ borderColor: "rgba(140,200,150,.3)" }}
                >
                  <span
                    className="h-[5px] w-[5px] rounded-full"
                    style={{ background: C.online }}
                  />
                  <span className="text-[9px]" style={{ color: C.onlineSoft }}>
                    {STATUS_TEXT[statuses[HUB_CHIEF.agentId]?.status ?? "idle"]}
                  </span>
                </span>
                <svg width="88" height="12" viewBox="0 0 88 12" className="hidden xl:block">
                  <polyline
                    points="0,6 6,6 10,2 14,10 18,4 22,8 26,3 30,9 34,5 38,7 42,1 46,11 50,6 54,6 58,4 62,8 66,6 70,6 74,3 78,9 82,6 88,6"
                    fill="none"
                    stroke="rgba(200,127,78,.55)"
                    strokeWidth="1"
                  />
                </svg>
              </span>
            </span>
          </div>

          <nav className="hidden items-center gap-1 lg:flex">
            {TOP_TABS.map((t) => (
              <Link
                key={t.label}
                href={t.href}
                className={cn(
                  "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[12px] transition-colors",
                  t.active ? "border" : "border border-transparent hover:opacity-80",
                )}
                style={
                  t.active
                    ? {
                        borderColor: "rgba(200,127,78,.4)",
                        background: "rgba(200,127,78,.12)",
                        color: C.copperLight,
                      }
                    : { color: C.warm }
                }
              >
                <span className="text-[12px] opacity-90">{t.icon}</span>
                <span className="hidden xl:inline">{t.label}</span>
              </Link>
            ))}
          </nav>

          <div className="flex shrink-0 items-center gap-[18px]">
            <span
              className="relative flex h-[34px] w-[34px] items-center justify-center rounded-full border text-[13px]"
              style={{ borderColor: "rgba(200,127,78,.22)" }}
            >
              🔔
              {stats.ceoNotifications > 0 ? (
                <span
                  className="absolute right-[3px] top-[2px] h-[6px] w-[6px] rounded-full"
                  style={{ background: C.copper, boxShadow: `0 0 6px ${C.copper}` }}
                />
              ) : null}
            </span>
            <span className="flex items-center gap-[9px]">
              <AgentAvatar agentId={HUB_OWNER.id} name={HUB_OWNER.name} size={36} />
              <span className="hidden xl:block">
                <span className="block text-[12px] font-medium">{HUB_OWNER.name}</span>
                <span className="block text-[9.5px]" style={{ color: C.dim }}>
                  {HUB_OWNER.role}
                </span>
              </span>
              <span className="text-[9px]" style={{ color: C.dim }}>
                ▾
              </span>
            </span>
          </div>
        </div>
      </header>

      {/* ══ BODY ══ */}
      <div className="flex min-h-[600px] flex-1">
        {/* SIDEBAR */}
        <aside
          className="flex w-[clamp(178px,13.7vw,210px)] shrink-0 flex-col gap-3 overflow-y-auto border-r px-3 py-4"
          style={{ borderColor: C.line }}
        >
          <SectionBox title="TABLEAU DE BORD">
            {DASHBOARD_NAV.map((it) => (
              <Link
                key={it.label}
                href={it.href}
                className="flex items-center justify-between gap-1 whitespace-nowrap rounded-[7px] px-2 py-[7px] text-[12px] transition-colors hover:bg-white/[0.03]"
                style={{ color: C.warm }}
              >
                <span className="flex min-w-0 items-center gap-2">
                  <span className="w-[15px] shrink-0 text-center text-[12px]" style={{ color: C.copper }}>
                    {it.icon}
                  </span>
                  {it.label}
                </span>
                {it.badge && stats.ceoNotifications > 0 ? (
                  <span
                    className="rounded-lg border px-1.5 text-[9px]"
                    style={{ borderColor: "rgba(200,127,78,.5)", color: C.copperLight }}
                  >
                    {stats.ceoNotifications}
                  </span>
                ) : null}
              </Link>
            ))}
          </SectionBox>

          <SectionBox title="DÉPARTEMENTS">
            {/* La maquette liste 10 bureaux opérationnels, sans "CEO" (page
                Mission Control bespoke, pas un département au même sens) —
                filtré ici uniquement pour ce rendu, CONSOLE_POLES lui-même
                (partagé par tout le Hub) n'est pas modifié. `pole.code` est
                assigné dans l'ordre du tableau complet (avec "ceo") : une
                fois filtré ici, ça laisse un trou ("02" puis "04") — la
                numérotation affichée est donc recalculée séquentiellement
                sur la liste déjà filtrée plutôt que de réutiliser ce code. */}
            {CONSOLE_POLES.filter((pole) => pole.id !== "ceo").map((pole, i) => {
              const active = pole.href === ROUTES.app;
              const icon = DEPT_ICON[pole.id] ?? "◈";
              return (
                <Link
                  key={pole.id}
                  href={pole.href}
                  className="flex items-center justify-between rounded-[7px] px-2 py-[7px] transition-colors hover:bg-white/[0.03]"
                  style={
                    active
                      ? { background: "rgba(200,127,78,.12)", color: C.copperLight }
                      : { color: C.warm }
                  }
                >
                  <span className="flex min-w-0 items-center gap-2">
                    <span className="w-[16px] shrink-0 text-center text-[11px]" style={{ color: C.copper }}>
                      {icon}
                    </span>
                    <span className="text-[10.5px]" style={{ color: C.faint }}>
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <span className="truncate text-[12px]">
                      {pole.name.replace("Bureau ", "").replace("Pôle ", "")}
                    </span>
                  </span>
                  <span className="text-[10px]" style={{ color: "#6E655E" }}>
                    ›
                  </span>
                </Link>
              );
            })}
          </SectionBox>

          <SectionBox title="OUTILS">
            {TOOLS_NAV.map((t) => (
              <Link
                key={t.label}
                href={t.href}
                className="flex items-center justify-between gap-1 whitespace-nowrap rounded-[7px] px-2 py-[7px] text-[12px] transition-colors hover:bg-white/[0.03]"
                style={{ color: C.warm }}
              >
                <span className="flex min-w-0 items-center gap-2">
                  <span className="w-[15px] shrink-0 text-center text-[11px]" style={{ color: C.copper }}>
                    {t.icon}
                  </span>
                  {t.label}
                </span>
                <span className="text-[10px]" style={{ color: "#6E655E" }}>
                  ›
                </span>
              </Link>
            ))}
          </SectionBox>

          {/* ALNUA CORE */}
          <div
            className="relative mt-auto overflow-hidden rounded-xl border p-3 pb-3.5"
            style={{
              borderColor: "rgba(200,127,78,.2)",
              background:
                "radial-gradient(120% 90% at 50% 45%, rgba(200,127,78,.13), rgba(12,10,9,.9) 70%)",
            }}
          >
            <div className="flex items-center justify-center gap-2">
              <span
                className="h-px w-4"
                style={{ background: "linear-gradient(90deg,transparent,rgba(200,127,78,.6))" }}
              />
              <span className="text-[10px] tracking-[2.4px]" style={{ color: C.copperLight }}>
                ALNUA CORE
              </span>
              <span
                className="h-px w-4"
                style={{ background: "linear-gradient(90deg,rgba(200,127,78,.6),transparent)" }}
              />
            </div>
            <p className="mt-[3px] text-center text-[9.5px]" style={{ color: C.dim }}>
              Système opérationnel
            </p>
            <div className="relative mt-1.5 flex h-[100px] items-center justify-center">
              <svg viewBox="0 0 168 112" className="absolute inset-0 m-auto h-full w-full" aria-hidden>
                <g fill="none" stroke="rgba(200,127,78,.35)">
                  <ellipse cx="84" cy="56" rx="78" ry="30" />
                  <ellipse cx="84" cy="56" rx="60" ry="46" stroke="rgba(200,127,78,.22)" />
                  <ellipse cx="84" cy="56" rx="44" ry="17" />
                  <ellipse cx="84" cy="56" rx="26" ry="34" stroke="rgba(200,127,78,.2)" />
                  <ellipse cx="84" cy="56" rx="20" ry="8" />
                </g>
                <circle cx="162" cy="56" r="2" fill={C.copperLight} />
                <circle cx="84" cy="10" r="1.8" fill={C.copper} />
                <circle cx="40" cy="56" r="1.6" fill={C.copper} />
              </svg>
              <AlnuaStar size={48} glow className="relative" sparkMid="#E8A87C" sparkOuter="#C87F4E" glowColorRgb="200,127,78" />
            </div>
            <div className="mt-0.5 flex items-center justify-center gap-2">
              <span
                className="h-[7px] w-[7px] shrink-0 rounded-full"
                style={{ background: C.online, boxShadow: `0 0 7px ${C.online}` }}
              />
              <p className="text-left text-[9.5px] leading-tight" style={{ color: "#9A9089" }}>
                Tous les systèmes
                <br />
                opérationnels
              </p>
            </div>
          </div>
        </aside>

        {/* MAIN */}
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
                      borderColor: "rgba(200,127,78,.4)",
                      background:
                        "radial-gradient(circle at 30% 20%, rgba(200,127,78,.25), rgba(15,12,10,.9))",
                      color: C.copperLight,
                    }}
                  >
                    ◧
                  </span>
                  <div className="min-w-0">
                    <h1 className="truncate text-[23px] leading-[1.1] tracking-[1px]">
                      <span className="font-bold">APP</span>{" "}
                      <span className="font-light tracking-[4px]" style={{ color: "#D8CFC4" }}>
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
                      borderColor: "rgba(200,127,78,.22)",
                      background: "rgba(16,13,11,.6)",
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
                      borderColor: "rgba(200,127,78,.45)",
                      background: "rgba(200,127,78,.08)",
                      color: C.copperLight,
                    }}
                  >
                    ＋ <span className="hidden sm:inline">Ajouter un agent</span>
                  </button>
                  <span
                    className="flex h-[30px] w-[30px] items-center justify-center rounded-lg border"
                    style={{ borderColor: "rgba(200,127,78,.2)", color: C.dim }}
                  >
                    ⋮
                  </span>
                </div>
              </div>

              {/* Onglets */}
              <div
                className="flex gap-[22px] overflow-x-auto border-b"
                style={{ borderColor: "rgba(200,127,78,.15)" }}
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
                        color: active ? "#F2E9DE" : C.faint,
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
                          ? "radial-gradient(120% 120% at 0% 0%, rgba(200,127,78,.12), rgba(16,13,11,.6) 60%)"
                          : "rgba(16,13,11,.45)",
                        boxShadow: active ? "0 0 22px rgba(200,127,78,.12)" : undefined,
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
                        <span className="shrink-0 text-[9.5px]" style={{ color: "#D8CFC4" }}>
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
                      <span className="mt-auto flex min-w-0 gap-1 border-t pt-1.5" style={{ borderColor: "rgba(200,127,78,.12)" }}>
                        {agent.skills.slice(0, 3).map((sk) => (
                          <span
                            key={sk}
                            className="min-w-0 truncate rounded-[5px] border px-[5px] py-px text-[8.5px]"
                            style={{
                              borderColor: "rgba(200,127,78,.2)",
                              background: "rgba(200,127,78,.05)",
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
                  style={{ borderColor: "rgba(200,127,78,.3)", background: "rgba(16,13,11,.3)" }}
                >
                  <span
                    className="flex h-[26px] w-[26px] items-center justify-center rounded-full border text-[14px]"
                    style={{ borderColor: "rgba(200,127,78,.35)", color: C.copperLight }}
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
              style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}
            >
              <div
                className="flex items-center justify-between border-b pb-[9px]"
                style={{ borderColor: C.lineSoft }}
              >
                <span className="text-[9.5px] tracking-[1.6px]" style={{ color: "#D8CFC4" }}>
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
                style={{ borderColor: "rgba(200,127,78,.22)", color: C.warm }}
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
              style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}
            >
              <div
                className="flex items-center justify-between border-b pb-[9px]"
                style={{ borderColor: C.lineSoft }}
              >
                <span className="text-[9.5px] tracking-[1.5px]" style={{ color: "#D8CFC4" }}>
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
                          ? { background: "rgba(200,127,78,.12)" }
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
                style={{ borderColor: "rgba(200,127,78,.22)", color: C.warm }}
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
                  "radial-gradient(120% 120% at 0% 0%, rgba(200,127,78,.08), rgba(16,13,11,.6) 55%)",
                boxShadow: "0 0 24px rgba(200,127,78,.07)",
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
                borderColor: "rgba(200,127,78,.28)",
                background:
                  "radial-gradient(60% 220% at 50% 50%, rgba(200,127,78,.14), rgba(14,11,9,.7) 70%)",
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
                      style={{ borderColor: "rgba(200,127,78,.28)", color: C.copperLight }}
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
                  "radial-gradient(circle, rgba(200,127,78,.30) 0%, rgba(200,127,78,.10) 45%, transparent 70%)",
              }}
            >
              <span
                className="absolute h-[76px] w-[76px] rounded-full border"
                style={{ borderColor: "rgba(200,127,78,.35)" }}
              />
              <AlnuaStar size={60} glow sparkMid="#E8A87C" sparkOuter="#C87F4E" glowColorRgb="200,127,78" />
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
      </div>
    </div>
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
