import type { BureauKey } from "@/lib/agent-bureau";
import { ROUTES } from "@/lib/routes";

export type DirectionLead = {
  dept: string;
  bureau: BureauKey | "ceo";
  agentId: string;
  name: string;
  role: string;
  href: string;
  agentsHint: string;
};

export const DIRECTION_LEADS: DirectionLead[] = [
  {
    dept: "CEO",
    bureau: "ceo",
    agentId: "coo",
    name: "Emilie",
    role: "Fondatrice & CEO",
    href: ROUTES.ceo,
    agentsHint: "Bureau du CEO",
  },
  {
    dept: "Direction",
    bureau: "hub",
    agentId: "coo",
    name: "Aria Voss",
    role: "COO — orchestration",
    href: ROUTES.hub,
    agentsHint: "5 agents",
  },
  {
    dept: "Secrétariat",
    bureau: "secretary",
    agentId: "secretary",
    name: "Nadia Faure",
    role: "Secrétaire de direction",
    href: ROUTES.secretary,
    agentsHint: "Nadia · Clara",
  },
  {
    dept: "Juridique",
    bureau: "legal",
    agentId: "legal_counsel",
    name: "Solène Hariri",
    role: "Avocate d'entreprise",
    href: ROUTES.legal,
    agentsHint: "UE · USA · Asie",
  },
  {
    dept: "R&D",
    bureau: "rd",
    agentId: "rnd_agent",
    name: "Alex Mercer",
    role: "Lab innovation",
    href: ROUTES.rd,
    agentsHint: "Dossiers",
  },
  {
    dept: "APP",
    bureau: "app",
    agentId: "dev_app",
    name: "Théo Laurent",
    role: "App Office",
    href: ROUTES.app,
    agentsHint: "Produit",
  },
  {
    dept: "Gaming",
    bureau: "gaming",
    agentId: "game_director",
    name: "Mira Chen",
    role: "Game Director",
    href: ROUTES.gaming,
    agentsHint: "Studio",
  },
  {
    dept: "Robo",
    bureau: "robo",
    agentId: "hardware",
    name: "Yuki Tanaka",
    role: "Hardware lead",
    href: ROUTES.robo,
    agentsHint: "Workshop",
  },
  {
    dept: "Comms",
    bureau: "marketing",
    agentId: "marketing",
    name: "Camille Rousseau",
    role: "Marketing",
    href: ROUTES.marketing,
    agentsHint: "Contenu",
  },
  {
    dept: "Finance",
    bureau: "finances",
    agentId: "accounting",
    name: "Jules Bernard",
    role: "Comptabilité",
    href: ROUTES.finances,
    agentsHint: "Budget",
  },
  {
    dept: "Analytics",
    bureau: "analytics",
    agentId: "analyst_business",
    name: "Layla Hassan",
    role: "Business analyst",
    href: ROUTES.analytics,
    agentsHint: "KPIs",
  },
];

export const DIRECTION_DOCS = [
  { name: "ROADMAP.md", href: ROUTES.docs },
  { name: "Manuel utilisateur", href: ROUTES.userManual },
  { name: "Installation", href: `${ROUTES.docs}/getting-started/installation` },
] as const;
