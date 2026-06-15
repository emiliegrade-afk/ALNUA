/**
 * Bureau agent routing — mirrors config/agent_personas.py (room field).
 * Each agent appears on exactly one department page.
 */
import type { DeptKey } from "@/lib/dept-colors";

export type BureauKey =
  | "hub"
  | "secretary"
  | "app"
  | "gaming"
  | "robo"
  | "marketing"
  | "rd"
  | "finances"
  | "analytics";

/** Department page → persona room id */
export const BUREAU_ROOMS: Record<BureauKey, string> = {
  hub: "direction",
  secretary: "secretary_office",
  app: "app_office",
  gaming: "gaming_studio",
  robo: "hardware_workshop",
  marketing: "comms_hub",
  rd: "rnd_lab",
  finances: "accounting_office",
  analytics: "analytics_room",
};

export interface BureauAgentDef {
  id: string;
  room: string;
  icon: string;
  name: string;
  role: string;
  branch: DeptKey;
  description: string;
  skills: string[];
}

/** Canonical agent cards — keep in sync with config/agent_personas.py */
export const BUREAU_AGENTS: BureauAgentDef[] = [
  // direction (/hub)
  {
    id: "coo",
    room: "direction",
    icon: "🎯",
    name: "Aria Voss",
    role: "COO — Chef d'orchestre",
    branch: "hub",
    description: "Orchestration globale, délégation et priorisation.",
    skills: ["Délégation", "Briefing", "Pipeline"],
  },
  {
    id: "secretary",
    room: "secretary_office",
    icon: "📎",
    name: "Nadia Faure",
    role: "Secrétaire de Direction",
    branch: "secretary",
    description: "Filtre, priorise et coordonne avant la direction opérationnelle.",
    skills: ["Emails", "Agenda", "Contrats"],
  },
  {
    id: "pm",
    room: "direction",
    icon: "📋",
    name: "Sam Rivera",
    role: "PM — Gestion de projet",
    branch: "hub",
    description: "Triage tickets, roadmap et suivi des livrables.",
    skills: ["Triage", "Roadmap", "Priorisation"],
  },
  {
    id: "spec",
    room: "direction",
    icon: "📝",
    name: "Léon Marchand",
    role: "Spec — Rédacteur de specs",
    branch: "hub",
    description: "Rédaction specs techniques et prompts Cursor.",
    skills: ["Specs", "Cursor", "Architecture"],
  },
  {
    id: "qa",
    room: "direction",
    icon: "🔍",
    name: "Alex Okafor",
    role: "QA — Tests & qualité",
    branch: "hub",
    description: "Analyse feedbacks, bugs et qualité produit.",
    skills: ["Feedback", "Bugs", "Tests"],
  },
  // app_office (/app)
  {
    id: "dev_app",
    room: "app_office",
    icon: "💻",
    name: "Théo Laurent",
    role: "Dev — Applications mobiles",
    branch: "app",
    description: "NUAWAY, Naïa App — mobile et intégrations.",
    skills: ["React Native", "API", "Pipeline"],
  },
  {
    id: "dev_backend",
    room: "app_office",
    icon: "🛠️",
    name: "Hao Chen",
    role: "Dev — Backend & API",
    branch: "app",
    description: "API, fondations backend et intégrations.",
    skills: ["FastAPI", "PostgreSQL", "Auth"],
  },
  // gaming_studio (/gaming)
  {
    id: "game_director",
    room: "gaming_studio",
    icon: "🎬",
    name: "Kai Ito",
    role: "Game Director",
    branch: "gaming",
    description: "Lore, quêtes et vision narrative Wyrdheim.",
    skills: ["Lore", "Quêtes", "Narration"],
  },
  {
    id: "dev_gaming",
    room: "gaming_studio",
    icon: "🕹️",
    name: "Suki Park",
    role: "Dev — Jeux vidéo",
    branch: "gaming",
    description: "Intégration UE5, Nwiro et builds gaming.",
    skills: ["UE5", "Nwiro", "C++"],
  },
  {
    id: "level_designer",
    room: "gaming_studio",
    icon: "🗺️",
    name: "Finn Larsen",
    role: "Level & Narrative Designer",
    branch: "gaming",
    description: "Niveaux jouables, arcs narratifs et balance.",
    skills: ["Level design", "Quêtes", "Narrative"],
  },
  // rnd_lab (/rd)
  {
    id: "brainstorm",
    room: "rnd_lab",
    icon: "💡",
    name: "Nova Drake",
    role: "Brainstorm — Idéation",
    branch: "rd",
    description: "Idéation latérale, concepts et veille créative.",
    skills: ["Idéation", "Concepts", "Brainstorm"],
  },
  {
    id: "rnd_agent",
    room: "rnd_lab",
    icon: "🔬",
    name: "Mira Chen",
    role: "R&D — Recherche autonome",
    branch: "rd",
    description: "Recherche marché, prototypes et dossiers R&D.",
    skills: ["Veille", "Dossiers", "Prototypes"],
  },
  // comms_hub (/marketing)
  {
    id: "marketing",
    room: "comms_hub",
    icon: "📣",
    name: "Lena Rousseau",
    role: "Marketing",
    branch: "marketing",
    description: "Stratégie contenu, campagnes et réseaux sociaux.",
    skills: ["SEO", "Social", "Campagnes"],
  },
  {
    id: "content",
    room: "comms_hub",
    icon: "✍️",
    name: "Eliot Marsh",
    role: "Content — Rédaction",
    branch: "marketing",
    description: "Posts, dev logs et contenu produit.",
    skills: ["Copywriting", "Posts", "Dev logs"],
  },
  // hardware_workshop (/robo)
  {
    id: "hardware",
    room: "hardware_workshop",
    icon: "🔧",
    name: "Viktor Stein",
    role: "Hardware",
    branch: "robo",
    description: "BOM, composants et architecture matérielle Eve.",
    skills: ["BOM", "PCB", "Sourcing"],
  },
  {
    id: "embedded_dev",
    room: "hardware_workshop",
    icon: "⚡",
    name: "Rin Nakamura",
    role: "Embedded Dev",
    branch: "robo",
    description: "Raspberry Pi, firmware et déploiements.",
    skills: ["Python", "Pi", "SSH"],
  },
  // accounting_office (/finances)
  {
    id: "accounting",
    room: "accounting_office",
    icon: "📒",
    name: "Jules Bernard",
    role: "Comptabilité",
    branch: "finances",
    description: "Comptabilité, équilibres et suivi financier.",
    skills: ["Compta", "Budget", "Clôture"],
  },
  {
    id: "controller",
    room: "accounting_office",
    icon: "📊",
    name: "Rémi Chassagne",
    role: "Contrôleur de Gestion",
    branch: "finances",
    description: "Contrôle de gestion, coûts LLM et prévisions.",
    skills: ["KPIs", "Forecast", "Coûts LLM"],
  },
  // analytics_room (/analytics)
  {
    id: "analyst_business",
    room: "analytics_room",
    icon: "📈",
    name: "Layla Hassan",
    role: "Business Analyst",
    branch: "analytics",
    description: "Données marché et recommandations stratégiques.",
    skills: ["Marché", "KPIs", "Stratégie"],
  },
  {
    id: "analyst_data",
    room: "analytics_room",
    icon: "📉",
    name: "Axel Roux",
    role: "Data Analyst — BI",
    branch: "analytics",
    description: "Dashboards, BI et qualité des données.",
    skills: ["BI", "Dashboards", "SQL"],
  },
];

export function getAgentsForBureau(bureau: BureauKey): BureauAgentDef[] {
  const room = BUREAU_ROOMS[bureau];
  return BUREAU_AGENTS.filter((a) => a.room === room);
}

export function getAgentById(id: string): BureauAgentDef | undefined {
  return BUREAU_AGENTS.find((a) => a.id === id);
}

export function countAgentsForBureau(bureau: BureauKey): number {
  return getAgentsForBureau(bureau).length;
}
