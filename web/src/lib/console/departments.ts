import {
  AppWindow,
  Calculator,
  Compass,
  Crown,
  FlaskConical,
  Gamepad2,
  Megaphone,
  Network,
  Palette,
  UserRound,
  type LucideIcon,
} from "lucide-react";
import {
  BUREAU_AGENTS,
  getAgentsForBureau,
  type BureauAgentDef,
  type BureauKey,
} from "@/lib/agent-bureau";
import { DEPT_COLORS, type DeptKey } from "@/lib/dept-colors";
import type { LobbyStats } from "@/lib/lobby-api";
import type { AgentStatus, AgentStatusKind } from "@/lib/openroom-api";
import type { ConsoleAgent, ConsoleAgentStatus, ConsoleDepartment } from "./types";

interface PoleDef {
  id: string;
  code: string;
  name: string;
  tagline: string;
  description: string;
  href: string;
  icon: LucideIcon;
  dept: DeptKey;
  bureau?: BureauKey;
  glow: string;
}

const POLES: PoleDef[] = [
  {
    id: "hub",
    code: "01",
    name: "Direction",
    tagline: "Orchestration · Spec · QA · PM",
    description:
      "Centre opérationnel ALNUA — COO, specs, qualité et gestion de projet.",
    href: "/hub",
    icon: Compass,
    dept: "hub",
    bureau: "hub",
    glow: "#ffa500",
  },
  {
    id: "secretary",
    code: "02",
    name: "Secrétariat",
    tagline: "Coordination · Agenda · Mails",
    description: "Nadia Faure — filtre, priorise et coordonne la direction.",
    href: "/secretary",
    icon: UserRound,
    dept: "secretary",
    bureau: "secretary",
    glow: "#B87333",
  },
  {
    id: "ceo",
    code: "03",
    name: "Bureau CEO",
    tagline: "Vision · Décisions · Brief",
    description: "Cockpit exécutif et décisions stratégiques.",
    href: "/ceo",
    icon: Crown,
    dept: "ceo",
    glow: "#ffa500",
  },
  {
    id: "rd",
    code: "04",
    name: "Pôle R&D",
    tagline: "Recherche · Idéation · Prototypes",
    description: "Laboratoire R&D — veille, dossiers et expérimentation.",
    href: "/rd",
    icon: FlaskConical,
    dept: "rd",
    bureau: "rd",
    glow: "#B87333",
  },
  {
    id: "app",
    code: "05",
    name: "Pôle APP",
    tagline: "Applications · Backend · Academy",
    description: "Développement applicatif web, mobile et formations.",
    href: "/app",
    icon: AppWindow,
    dept: "app",
    bureau: "app",
    glow: "#b87333",
  },
  {
    id: "gaming",
    code: "06",
    name: "Pôle Gaming",
    tagline: "Studio · Lore · Godot",
    description: "Studio jeu — Wyrdheim, level design et dev gaming.",
    href: "/gaming",
    icon: Gamepad2,
    dept: "gaming",
    bureau: "gaming",
    glow: "#ffa500",
  },
  {
    id: "robo",
    code: "07",
    name: "Robotique",
    tagline: "Hardware · Embedded · Eve",
    description: "Atelier hardware et firmware embarqué.",
    href: "/robo",
    icon: Network,
    dept: "robo",
    bureau: "robo",
    glow: "#a7adb5",
  },
  {
    id: "marketing",
    code: "08",
    name: "Marketing",
    tagline: "Contenu · Campagnes · Social",
    description: "Comms Hub — marketing et rédaction produit.",
    href: "/marketing",
    icon: Megaphone,
    dept: "marketing",
    bureau: "marketing",
    glow: "#B87333",
  },
  {
    id: "finances",
    code: "09",
    name: "Comptabilité",
    tagline: "Finance · Coûts LLM · Contrôle",
    description: "Comptabilité et contrôle de gestion ALNUA.",
    href: "/finances",
    icon: Calculator,
    dept: "finances",
    bureau: "finances",
    glow: "#b87333",
  },
  {
    id: "analytics",
    code: "10",
    name: "Analytics",
    tagline: "BI · Data · Stratégie",
    description: "Analyse business et data pour la direction.",
    href: "/analytics",
    icon: Compass,
    dept: "analytics",
    bureau: "analytics",
    glow: "#B87333",
  },
  {
    id: "brand",
    code: "11",
    name: "Brand Design",
    tagline: "Identité · Kits · Assets",
    description: "Brand kits, palettes et assets visuels.",
    href: "/brand",
    icon: Palette,
    dept: "brand",
    glow: "#d4c98a",
  },
];

function mapStatus(kind: AgentStatusKind | undefined): ConsoleAgentStatus {
  switch (kind) {
    case "working":
      return "active";
    case "waiting":
      return "thinking";
    case "error":
      return "review";
    default:
      return "idle";
  }
}

function utilizationFor(status: AgentStatusKind | undefined, progress?: number): number {
  if (typeof progress === "number") return Math.min(100, Math.max(0, progress));
  switch (status) {
    case "working":
      return 78;
    case "waiting":
      return 48;
    case "error":
      return 35;
    default:
      return 12;
  }
}

function initials(name: string): string {
  return name
    .split(" ")
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

function agentsForPole(
  pole: PoleDef,
  live: Record<string, AgentStatus>,
): ConsoleAgent[] {
  const defs: BureauAgentDef[] = pole.bureau
    ? getAgentsForBureau(pole.bureau)
    : BUREAU_AGENTS.filter((a) => {
        if (pole.id === "ceo") return a.id === "coo";
        return false;
      });

  return defs.map((agent) => {
    const liveAgent = live[agent.id];
    const status = mapStatus(liveAgent?.status);
    return {
      id: agent.id,
      name: agent.name,
      role: agent.role,
      specialty: agent.skills.slice(0, 2).join(" · "),
      status,
      model: "OpenRouter",
      utilization: utilizationFor(liveAgent?.status, liveAgent?.progress),
      task: liveAgent?.currentTask ?? "En veille — prêt pour dispatch",
      initials: initials(agent.name),
      hue: DEPT_COLORS[pole.dept].main,
    };
  });
}

function kpisForPole(pole: PoleDef, stats: LobbyStats): { label: string; value: string }[] {
  switch (pole.id) {
    case "hub":
      return [
        { label: "PRs ouverts", value: String(stats.hubPrCount) },
        { label: "API Hub", value: stats.apiOnline ? "En ligne" : "Hors ligne" },
        { label: "Auth", value: stats.apiAuthenticated ? "OK" : "—" },
      ];
    case "app":
      return [
        { label: "Tickets ouverts", value: String(stats.appOpenTickets) },
        { label: "Apps connectées", value: String(stats.connectedApps) },
        { label: "Brand kits", value: String(stats.brandKits) },
      ];
    case "rd":
      return [
        { label: "Sessions R&D", value: String(stats.rdSessions) },
        { label: "Pipeline", value: stats.apiOnline ? "Actif" : "Pause" },
        { label: "Veille", value: "Live" },
      ];
    case "marketing":
      return [
        { label: "Posts en attente", value: String(stats.marketingPendingPosts) },
        { label: "Contenu", value: "Hub" },
        { label: "Campagnes", value: "—" },
      ];
    case "finances":
      return [
        { label: "Mois en cours", value: stats.financesMonthTotal },
        { label: "Coût LLM / jour", value: `$${stats.costTodayUsd.toFixed(2)}` },
        { label: "Budget", value: "Suivi actif" },
      ];
    case "gaming":
      return [
        { label: "Statut studio", value: stats.gamingStatus.slice(0, 24) },
        { label: "Builds", value: "—" },
        { label: "Assets", value: "—" },
      ];
    case "robo":
      return [
        { label: "Prototype", value: stats.roboStatus.slice(0, 24) },
        { label: "Firmware", value: "—" },
        { label: "BOM", value: "—" },
      ];
    default:
      return [
        { label: "Agents", value: String(agentsForPole(pole, {}).length) },
        { label: "Statut", value: stats.apiOnline ? "Opérationnel" : "Dégradé" },
        { label: "Sync", value: "Temps réel" },
      ];
  }
}

const DEFAULT_PROJECTS: ConsoleDepartment["projects"] = [
  { name: "Pipeline en cours", progress: 62, status: "on-track" },
  { name: "Revue qualité", progress: 38, status: "review" },
];

export function buildConsoleDepartments(
  liveAgents: Record<string, AgentStatus>,
  stats: LobbyStats,
): ConsoleDepartment[] {
  return POLES.map((pole) => ({
    id: pole.id,
    code: pole.code,
    name: pole.name,
    tagline: pole.tagline,
    description: pole.description,
    href: pole.href,
    icon: pole.icon,
    accent: "text-bronze-bright",
    ring: "ring-bronze/40",
    glow: pole.glow,
    agents: agentsForPole(pole, liveAgents),
    kpis: kpisForPole(pole, stats),
    projects: DEFAULT_PROJECTS,
  }));
}

export function getConsoleDepartment(
  id: string,
  liveAgents: Record<string, AgentStatus>,
  stats: LobbyStats,
): ConsoleDepartment | undefined {
  return buildConsoleDepartments(liveAgents, stats).find((d) => d.id === id);
}

export function getConsoleDepartmentByHref(
  href: string,
  liveAgents: Record<string, AgentStatus>,
  stats: LobbyStats,
): ConsoleDepartment | undefined {
  return buildConsoleDepartments(liveAgents, stats).find((d) => d.href === href);
}

/** Static pole list for sidebar icons (no live merge needed). */
export const CONSOLE_POLES = POLES;
