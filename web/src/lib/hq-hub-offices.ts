import type { BureauKey } from "@/lib/agent-bureau";
import {
  countAgentsForBureau,
  getAgentById,
  getAgentsForBureau,
  type BureauAgentDef,
} from "@/lib/agent-bureau";
import type { DeptKey } from "@/lib/dept-colors";
import type { LobbyStats } from "@/lib/lobby-api";

/** Shared sector metadata (map + off-map). */
export interface HqSectorBase {
  id: string;
  number: number;
  title: string;
  shortcutLabel: string;
  subtitle: string;
  href: string;
  icon: string;
  dept: DeptKey;
  bureau?: BureauKey;
  primaryAgentId?: string;
}

/** Office drawn on the floor plan — hotspot required. */
export interface HqMapOffice extends HqSectorBase {
  x: number;
  y: number;
  w: number;
  h: number;
  level: "ground" | "mezzanine";
}

/** Sector without a room on the image — sidebar / command deck only. */
export interface HqOffMapAccess extends HqSectorBase {
  portrait?: string;
}

export type HqSector = HqMapOffice | HqOffMapAccess;

/** @deprecated Use HqMapOffice or HqSector */
export type HqOfficeDef = HqSector;

export function isMapOffice(sector: HqSector): sector is HqMapOffice {
  return "x" in sector;
}

export const HQ_HUB_IMAGE_WEBP = "/environments/hq-hub-17-offices.webp?v=1";
export const HQ_HUB_IMAGE = "/environments/hq-hub-17-offices.png?v=1";

/** Native asset ratio — 3:2, never center-crop the file. */
export const HQ_HUB_ASPECT = 1536 / 1024;

/**
 * v17 hotspots — center x/y + w/h in % on the 1536×1024 artwork.
 * Calibrated on glass façades facing the atrium (entrées visibles).
 */
export const HQ_MAP_OFFICES: HqMapOffice[] = [
  {
    id: "meeting",
    number: 0,
    title: "Salle de réunion",
    shortcutLabel: "Réunion",
    subtitle: "Briefings · Sessions équipe",
    href: "/briefing",
    icon: "🤝",
    dept: "hub",
    x: 15.5,
    y: 38,
    w: 18,
    h: 15,
    level: "ground",
  },
  {
    id: "secretary",
    number: 2,
    title: "Secrétariat",
    shortcutLabel: "Secrétariat",
    subtitle: "Nadia Faure · Ta secrétaire · mails & planning",
    href: "/secretary",
    icon: "📎",
    dept: "secretary",
    bureau: "secretary",
    primaryAgentId: "secretary",
    x: 35.5,
    y: 34.5,
    w: 10,
    h: 10,
    level: "ground",
  },
  {
    id: "ceo",
    number: 1,
    title: "CEO Office",
    shortcutLabel: "CEO",
    subtitle: "Emilie · Brief & décisions",
    href: "/ceo",
    icon: "👑",
    dept: "ceo",
    x: 49.5,
    y: 31,
    w: 13,
    h: 10,
    level: "ground",
  },
  {
    id: "direction",
    number: 3,
    title: "Direction",
    shortcutLabel: "Direction",
    subtitle: "Aria · Sam · Léon · Alex",
    href: "/hub",
    icon: "🏛️",
    dept: "hub",
    bureau: "hub",
    primaryAgentId: "coo",
    x: 82.5,
    y: 37.5,
    w: 16,
    h: 13,
    level: "ground",
  },
  {
    id: "dev_lounge",
    number: 0,
    title: "Espace détente",
    shortcutLabel: "Détente",
    subtitle: "Pause · Café · Open space",
    href: "/openroom",
    icon: "☕",
    dept: "lounge",
    x: 50,
    y: 56.5,
    w: 19,
    h: 13,
    level: "ground",
  },
  {
    id: "gaming",
    number: 5,
    title: "Gaming Studio",
    shortcutLabel: "Gaming",
    subtitle: "Wyrdheim · Lore",
    href: "/gaming",
    icon: "🎮",
    dept: "gaming",
    bureau: "gaming",
    primaryAgentId: "game_director",
    x: 17.5,
    y: 77.5,
    w: 12,
    h: 10.5,
    level: "ground",
  },
  {
    id: "app",
    number: 4,
    title: "App Dev",
    shortcutLabel: "App Dev",
    subtitle: "Théo · Hao · Mobile & API",
    href: "/app",
    icon: "📱",
    dept: "app",
    bureau: "app",
    primaryAgentId: "dev_app",
    x: 50,
    y: 79.5,
    w: 13,
    h: 10,
    level: "ground",
  },
  {
    id: "robo",
    number: 6,
    title: "Robotics Lab",
    shortcutLabel: "Robotics",
    subtitle: "Eve · Hardware · Embedded",
    href: "/robo",
    icon: "🤖",
    dept: "robo",
    bureau: "robo",
    primaryAgentId: "hardware",
    x: 82.5,
    y: 77.5,
    w: 12,
    h: 10.5,
    level: "ground",
  },
  {
    id: "finances",
    number: 7,
    title: "Finance",
    shortcutLabel: "Finance",
    subtitle: "Jules · Rémi · Budget",
    href: "/finances",
    icon: "💰",
    dept: "finances",
    bureau: "finances",
    primaryAgentId: "accounting",
    x: 14.5,
    y: 13,
    w: 11,
    h: 11,
    level: "mezzanine",
  },
  {
    id: "marketing",
    number: 8,
    title: "Marketing",
    shortcutLabel: "Marketing",
    subtitle: "Lena · Eliot · Contenu",
    href: "/marketing",
    icon: "📣",
    dept: "marketing",
    bureau: "marketing",
    primaryAgentId: "marketing",
    x: 26,
    y: 12.5,
    w: 11,
    h: 11,
    level: "mezzanine",
  },
  {
    id: "rd",
    number: 9,
    title: "R&D Lab",
    shortcutLabel: "R&D",
    subtitle: "Nova · Mira · Dossiers",
    href: "/rd",
    icon: "🔬",
    dept: "rd",
    bureau: "rd",
    primaryAgentId: "rnd_agent",
    x: 38,
    y: 12,
    w: 11,
    h: 11,
    level: "mezzanine",
  },
  {
    id: "academy",
    number: 13,
    title: "ALNUA Academy",
    shortcutLabel: "Academy",
    subtitle: "Entraînement · Niveaux · Sprints agents",
    href: "/academy",
    icon: "🎓",
    dept: "academy",
    primaryAgentId: "qa",
    x: 50,
    y: 8.5,
    w: 13,
    h: 7.5,
    level: "mezzanine",
  },
  {
    id: "brand",
    number: 10,
    title: "Brand Studio",
    shortcutLabel: "Brand",
    subtitle: "Brand Kit · Charte",
    href: "/brand",
    icon: "🎨",
    dept: "brand",
    x: 62,
    y: 12.5,
    w: 11,
    h: 11,
    level: "mezzanine",
  },
  {
    id: "analytics",
    number: 11,
    title: "Analytics",
    shortcutLabel: "Analytics",
    subtitle: "Layla · Axel · KPIs",
    href: "/analytics",
    icon: "📊",
    dept: "analytics",
    bureau: "analytics",
    primaryAgentId: "analyst_business",
    x: 74.5,
    y: 13,
    w: 11,
    h: 11,
    level: "mezzanine",
  },
  {
    id: "connections",
    number: 12,
    title: "IT Connections",
    shortcutLabel: "IT",
    subtitle: "OAuth · Intégrations",
    href: "/connections",
    icon: "🔌",
    dept: "it",
    x: 87,
    y: 13,
    w: 11,
    h: 11,
    level: "mezzanine",
  },
];

/** Quick-access shortcuts not duplicated on map (empty when all rooms are on artwork). */
export const HQ_OFF_MAP_ACCESS: HqOffMapAccess[] = [
  {
    id: "library",
    number: 14,
    title: "Bibliothèque",
    shortcutLabel: "Bibliothèque",
    subtitle: "Recherche · archives · rapport CEO",
    href: "/library",
    icon: "📚",
    dept: "hub",
  },
  {
    id: "ide",
    number: 16,
    title: "IDE Hub",
    shortcutLabel: "IDE",
    subtitle: "Monaco · Bac à sable · Luca",
    href: "/ide",
    icon: "💻",
    dept: "academy",
  },
  {
    id: "admin",
    number: 15,
    title: "Admin",
    shortcutLabel: "Admin",
    subtitle: "Coûts LLM · événements · A/B tests",
    href: "/admin",
    icon: "⚙️",
    dept: "hub",
  },
];

export const HQ_CEO_ACCESS: HqOffMapAccess = {
  id: "ceo",
  number: 1,
  title: "CEO Office",
  shortcutLabel: "CEO",
  subtitle: "Emilie · Brief & décisions",
  href: "/ceo",
  icon: "👑",
  dept: "ceo",
  portrait: "/agents/ceo/office.png",
};

/** @deprecated Use HQ_MAP_OFFICES */
export const HQ_OFFICES = HQ_MAP_OFFICES;

export function getPrimaryAgentForOffice(
  office: HqSector,
): BureauAgentDef | null {
  if (office.primaryAgentId) {
    return getAgentById(office.primaryAgentId) ?? null;
  }
  if (office.bureau) {
    const agents = getAgentsForBureau(office.bureau);
    return agents[0] ?? null;
  }
  return null;
}

export interface HqOfficeBadge {
  label: string;
  highlight?: boolean;
}

export function getOfficeBadge(
  office: HqSector,
  stats: LobbyStats,
): HqOfficeBadge {
  switch (office.id) {
    case "ceo":
      return stats.ceoNotifications > 0
        ? { label: `${stats.ceoNotifications} notif`, highlight: true }
        : { label: "CEO" };
    case "secretary":
      return { label: `${countAgentsForBureau("secretary")} agent` };
    case "direction":
      return stats.hubPrCount > 0
        ? { label: `${stats.hubPrCount} PR`, highlight: true }
        : { label: `${countAgentsForBureau("hub")} agents` };
    case "app":
      return stats.appOpenTickets > 0
        ? { label: `${stats.appOpenTickets} tickets`, highlight: true }
        : { label: `${countAgentsForBureau("app")} agents` };
    case "gaming":
      return { label: `${countAgentsForBureau("gaming")} agents` };
    case "robo":
      return { label: "2 agents" };
    case "finances":
      return { label: stats.financesMonthTotal };
    case "marketing":
      return stats.marketingPendingPosts > 0
        ? { label: `${stats.marketingPendingPosts} posts`, highlight: true }
        : { label: `${countAgentsForBureau("marketing")} agents` };
    case "rd":
      return stats.rdSessions > 0
        ? { label: `${stats.rdSessions} sessions`, highlight: true }
        : { label: `${countAgentsForBureau("rd")} agents` };
    case "brand":
      return stats.brandKits > 0
        ? { label: `${stats.brandKits} kits`, highlight: true }
        : { label: "Brand" };
    case "analytics":
      return { label: `${countAgentsForBureau("analytics")} agents` };
    case "connections":
      return { label: `${stats.connectedApps} apps` };
    case "meeting":
      return { label: "Briefing" };
    case "academy":
      return { label: "Training" };
    case "ide":
      return { label: "IDE" };
    case "library":
      return { label: "Archives" };
    case "admin":
      return { label: "Outils" };
    case "dev_lounge":
      return { label: "Détente" };
    default:
      return { label: "" };
  }
}
