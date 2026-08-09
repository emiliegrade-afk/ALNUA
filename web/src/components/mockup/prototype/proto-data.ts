export type ProtoAgent = {
  id: string;
  initials: string;
  name: string;
  role: string;
  status: string;
  color: string;
};

export type ProtoProject = {
  name: string;
  type: string;
  progress: number;
  sprint: string;
  status: string;
  agents: number;
  tasks: number;
  updates: number;
  phase: number;
  image: string;
};

export type ProtoMission = {
  title: string;
  status: "backlog" | "progress" | "review" | "done";
  priority: string;
  tags: string[];
  progress: number;
  people: string[];
};

export type ProtoIdea = {
  title: string;
  desc: string;
  score: number;
  verdict: string;
  market: number;
  tech: number;
  business: number;
};

export const agents: ProtoAgent[] = [
  { id: "aria", initials: "AV", name: "Aria Voss", role: "COO · Chef d'orchestre", status: "online", color: "rose" },
  { id: "sam", initials: "SR", name: "Sam Rivera", role: "PM · Gestion de projet", status: "online", color: "blue" },
  { id: "theo", initials: "TL", name: "Théo Laurent", role: "Dev · Applications mobiles", status: "active", color: "violet" },
  { id: "ines", initials: "IM", name: "Inès Moreau", role: "UI/UX Designer", status: "active", color: "gold" },
  { id: "hao", initials: "HC", name: "Hao Chen", role: "Dev · Backend & API", status: "online", color: "cyan" },
  { id: "rayan", initials: "RK", name: "Rayan Koné", role: "DevOps · Intégration", status: "online", color: "green" },
  { id: "nova", initials: "NF", name: "Nova Fischer", role: "R&D · Recherche autonome", status: "online", color: "silver" },
  { id: "mira", initials: "MC", name: "Mira Chen", role: "Innovation · Concepts", status: "online", color: "rose" },
  { id: "layla", initials: "LH", name: "Layla Hassan", role: "Analyst Business", status: "online", color: "blue" },
  { id: "alex", initials: "AO", name: "Alex Okafor", role: "QA", status: "online", color: "cyan" },
];

export const projects: ProtoProject[] = [
  { name: "NAÏA", type: "Assistant IA · FemTech", progress: 83, sprint: "Sprint 18", status: "En développement", agents: 6, tasks: 128, updates: 24, phase: 2, image: "naia" },
  { name: "NUAWAY", type: "Plateforme Vanlife", progress: 61, sprint: "Sprint 12", status: "En développement", agents: 3, tasks: 48, updates: 12, phase: 2, image: "nuaway" },
  { name: "Academy", type: "Plateforme de formation", progress: 94, sprint: "Sprint 7", status: "En validation", agents: 4, tasks: 36, updates: 8, phase: 3, image: "academy" },
  { name: "ALNUA Hub", type: "Plateforme centrale", progress: 97, sprint: "Stable", status: "Stable", agents: 7, tasks: 22, updates: 15, phase: 4, image: "hub" },
  { name: "Nwiro", type: "Application Mindset", progress: 43, sprint: "Sprint 5", status: "En développement", agents: 2, tasks: 18, updates: 6, phase: 2, image: "nwiro" },
  { name: "IA Core", type: "Moteur d'intelligence", progress: 71, sprint: "Sprint 9", status: "En développement", agents: 5, tasks: 64, updates: 14, phase: 2, image: "core" },
  { name: "Robotique", type: "Systèmes robotiques", progress: 28, sprint: "Recherche", status: "Recherche", agents: 1, tasks: 9, updates: 2, phase: 0, image: "robot" },
];

export const missions: ProtoMission[] = [
  { title: "Feature request: Dark mode enhancements", status: "backlog", priority: "Haute", tags: ["React", "Node"], progress: 77, people: ["ines", "theo", "hao"] },
  { title: "Feature request: Notifications systems", status: "backlog", priority: "Moyenne", tags: ["React", "API"], progress: 52, people: ["theo", "hao"] },
  { title: "Database Migration", status: "progress", priority: "Haute", tags: ["Node", "PostgreSQL"], progress: 78, people: ["hao", "rayan", "theo"] },
  { title: "User Auth Refactor", status: "progress", priority: "Haute", tags: ["React", "Node", "Expo"], progress: 70, people: ["hao", "theo"] },
  { title: "QA for API v2", status: "review", priority: "Moyenne", tags: ["API", "Tests"], progress: 76, people: ["alex", "theo"] },
  { title: "UI Design — new profile page", status: "review", priority: "Moyenne", tags: ["UI", "Figma"], progress: 93, people: ["ines"] },
  { title: "MessageList component", status: "done", priority: "Basse", tags: ["React", "Node"], progress: 76, people: ["theo"] },
  { title: "Notifications system", status: "done", priority: "Moyenne", tags: ["React", "Node"], progress: 53, people: ["theo", "hao"] },
];

export const ideas: ProtoIdea[] = [
  { title: "NUA Copilot Mobile", desc: "Assistant IA nomade hors ligne pour créateurs de contenu.", score: 92, verdict: "GO", market: 9, tech: 10, business: 8 },
  { title: "Robot Companion", desc: "Compagnon robotique IA pour la maison et la mobilité.", score: 74, verdict: "MAYBE", market: 8, tech: 8, business: 6 },
  { title: "Marketplace IA", desc: "Plateforme de modèles et compétences IA pour entreprises.", score: 61, verdict: "NO", market: 6, tech: 7, business: 4 },
  { title: "Wyrdheim Online", desc: "MMORPG nouvelle génération avec IA vivante.", score: 88, verdict: "GO", market: 9, tech: 9, business: 8 },
  { title: "Health AI Companion", desc: "Coach santé IA personnalisé qui vous comprend.", score: 79, verdict: "MAYBE", market: 8, tech: 7, business: 7 },
  { title: "Energy Hub", desc: "Station d'énergie autonome intelligente et durable.", score: 46, verdict: "NO", market: 5, tech: 6, business: 4 },
];

export const brainstorm: [string, string][] = [
  ["Aria", "Je pense que le marché des créateurs nomades IA va exploser en 2026."],
  ["Nova", "Techniquement, c'est totalement faisable avec des modèles légers embarqués."],
  ["Layla", "Le marché semble prometteur, mais la concurrence est déjà présente."],
  ["Axel", "Les données montrent une croissance de +28% sur ce segment."],
  ["Mira", "Je propose un MVP centré sur la création de contenu assistée hors ligne."],
];
