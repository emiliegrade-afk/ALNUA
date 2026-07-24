/**
 * ALNUA — Rich operational data for the domotic-style console.
 * Adds system metrics, charts series, incidents, deployments, decisions,
 * milestones, activity heatmap, agent communication graph, and per-pôle
 * budget / capabilities / sensors / performance / agent metrics.
 *
 * Kept separate from alnua-data.ts so the core domain model stays stable.
 */

// ─── Real-time system metrics ────────────────────────────────────────────────
export interface Metric {
  value: number;
  label: string;
  unit: string;
  trend: number[];
  /** copper = LLM/cost-related, titanium = infra/system-related. */
  tone?: "copper" | "titanium";
}

export const systemMetrics: Record<string, Metric> = {
  cpu: { value: 47, label: "CPU", unit: "%", trend: [40, 42, 45, 43, 47, 46, 48, 47, 45, 47] },
  memory: { value: 63, label: "Mémoire", unit: "%", trend: [55, 58, 60, 62, 63, 61, 63, 62, 63, 63] },
  network: { value: 28, label: "Réseau", unit: "Gb/s", trend: [22, 25, 28, 26, 28, 30, 28, 27, 29, 28] },
  edge: { value: 12, label: "Latence edge", unit: "ms", trend: [14, 13, 12, 12, 11, 12, 13, 12, 12, 12] },
  gpu: { value: 81, label: "GPU cluster", unit: "%", trend: [70, 75, 78, 80, 81, 79, 82, 81, 80, 81] },
  storage: { value: 38, label: "Stockage", unit: "%", trend: [30, 32, 35, 36, 37, 38, 38, 37, 38, 38] },
};

// ─── Revenue (12 months, k€) ────────────────────────────────────────────────
export const revenueSeries = [
  { label: "Jan", value: 142 }, { label: "Fév", value: 168 },
  { label: "Mar", value: 195 }, { label: "Avr", value: 210 },
  { label: "Mai", value: 248 }, { label: "Juin", value: 272 },
  { label: "Juil", value: 305 }, { label: "Août", value: 298 },
  { label: "Sep", value: 342 }, { label: "Oct", value: 388 },
  { label: "Nov", value: 421 }, { label: "Déc", value: 472 },
];

// ─── 24h activity (requests/agents active per hour, normalized 0-100) ───────
export const activity24h = [12, 8, 5, 3, 2, 4, 9, 18, 24, 28, 31, 29, 27, 30, 33, 35, 32, 28, 24, 22, 19, 16, 14, 13];

// ─── Decisions over 7 days ──────────────────────────────────────────────────
export const decisions7d = [
  { label: "Lun", value: 168 }, { label: "Mar", value: 192 },
  { label: "Mer", value: 175 }, { label: "Jeu", value: 210 },
  { label: "Ven", value: 184 }, { label: "Sam", value: 95 },
  { label: "Dim", value: 72 },
];

// ─── World clocks ───────────────────────────────────────────────────────────
export const timezones = [
  { city: "Paris", tz: "Europe/Paris", code: "FR" },
  { city: "New York", tz: "America/New_York", code: "US" },
  { city: "Tokyo", tz: "Asia/Tokyo", code: "JP" },
  { city: "Dubaï", tz: "Asia/Dubai", code: "AE" },
];

// ─── Incidents ──────────────────────────────────────────────────────────────
export type Severity = "info" | "warning" | "critical";
export interface Incident {
  id: string;
  severity: Severity;
  title: string;
  pôle: string;
  time: string;
  resolved: boolean;
}
export const incidents: Incident[] = [
  { id: "i1", severity: "info", title: "Déploiement NAÏA v2.4 réussi", pôle: "APP", time: "il y a 2 min", resolved: true },
  { id: "i2", severity: "warning", title: "Latence edge US-Ouest élevée (24ms)", pôle: "CONNECTIVITÉ", time: "il y a 8 min", resolved: false },
  { id: "i3", severity: "critical", title: "Tentative d'intrusion neutralisée", pôle: "CONNECTIVITÉ", time: "il y a 9 min", resolved: true },
  { id: "i4", severity: "info", title: "Sauvegarde Q2 terminée (4.2 Go)", pôle: "COMPTA", time: "il y a 25 min", resolved: true },
  { id: "i5", severity: "warning", title: "GPU cluster à 81% — scale-up recommandé", pôle: "R&D", time: "il y a 40 min", resolved: false },
  { id: "i6", severity: "info", title: "Calibration bras EVE-X terminée", pôle: "ROBOTIQUE", time: "il y a 52 min", resolved: true },
];

// ─── Deployments ────────────────────────────────────────────────────────────
export type DeployStatus = "success" | "running" | "failed";
export interface Deployment {
  id: string;
  service: string;
  version: string;
  status: DeployStatus;
  time: string;
  by: string;
}
export const deployments: Deployment[] = [
  { id: "d1", service: "naia-api", version: "v2.4.1", status: "success", time: "12:42", by: "LOOM" },
  { id: "d2", service: "alnua-console", version: "v1.0.8", status: "success", time: "12:18", by: "FORGE" },
  { id: "d3", service: "eve-engine", version: "v0.9.2-β", status: "running", time: "11:55", by: "RENDER" },
  { id: "d4", service: "edge-eu-west", version: "v3.1.0", status: "success", time: "10:30", by: "EDGE" },
  { id: "d5", service: "nomad-firmware", version: "v0.4.0", status: "failed", time: "09:12", by: "KILO" },
  { id: "d6", service: "marketing-cms", version: "v1.2.0", status: "success", time: "08:48", by: "VIRAL" },
];

// ─── Today's decisions pipeline ─────────────────────────────────────────────
export type DecisionStatus = "approved" | "review" | "pending";
export interface Decision {
  id: string;
  agent: string;
  title: string;
  status: DecisionStatus;
  time: string;
  impact: "high" | "medium" | "low";
}
export const decisionsToday: Decision[] = [
  { id: "dec1", agent: "ATLAS Prime", title: "Valider la feuille de route Q3 2026", status: "approved", time: "11:42", impact: "high" },
  { id: "dec2", agent: "ORION", title: "Réallouer 2 agents R&D → pôle APP", status: "approved", time: "10:28", impact: "medium" },
  { id: "dec3", agent: "LEDGER", title: "Augmenter le budget marketing de 12%", status: "review", time: "09:55", impact: "medium" },
  { id: "dec4", agent: "CIPHER", title: "Bloquer l'IP suspicieuse 89.x.x.x", status: "approved", time: "09:12", impact: "high" },
  { id: "dec5", agent: "AURA-DA", title: "Finaliser la charte graphique ALNUA", status: "approved", time: "08:48", impact: "medium" },
  { id: "dec6", agent: "PROMÉTHÉE", title: "Lancer l'expérience fusion vision-texte", status: "pending", time: "08:20", impact: "low" },
];

// ─── Upcoming milestones ────────────────────────────────────────────────────
export interface Milestone {
  id: string;
  title: string;
  date: string;
  pôle: string;
  days: number;
}
export const milestones: Milestone[] = [
  { id: "m1", title: "Lancement teaser NAÏA", date: "12 juil", pôle: "MARKETING", days: 3 },
  { id: "m2", title: "Clôture trimestrielle Q2", date: "30 juil", pôle: "COMPTA", days: 21 },
  { id: "m3", title: "POC NOMAD embarqué", date: "15 août", pôle: "R&D", days: 37 },
  { id: "m4", title: "Calibration finale EVE-X", date: "22 août", pôle: "ROBOTIQUE", days: 44 },
  { id: "m5", title: "App NAÏA — bêta publique", date: "5 sep", pôle: "APP", days: 58 },
  { id: "m6", title: "Identité visuelle EVE", date: "18 sep", pôle: "ARTISTIQUE", days: 71 },
];

// ─── Agent communication graph ──────────────────────────────────────────────
// Edges are the real pipeline pairings documented per agent (each persona's
// system prompt names its counterpart) — not a live-measured interaction
// count, since inter-agent messages aren't logged with volume yet. Weight is
// left uniform rather than invented to avoid implying a measured intensity
// that doesn't exist.
export interface CommEdge { from: string; to: string; weight: number }
export const agentComm: CommEdge[] = [
  { from: "Aria (COO)", to: "Léon (Spec)", weight: 5 },
  { from: "Aria (COO)", to: "Sam (PM)", weight: 5 },
  { from: "Aria (COO)", to: "Nadia (Secrétaire)", weight: 5 },
  { from: "Léon (Spec)", to: "Alex O. (QA)", weight: 5 },
  { from: "Sam (PM)", to: "Théo (Dev App)", weight: 5 },
  { from: "Sam (PM)", to: "Hao (Dev Backend)", weight: 5 },
  { from: "Théo (Dev App)", to: "Hao (Dev Backend)", weight: 5 },
  { from: "Mira (Game Director)", to: "Nova (Dev Gaming)", weight: 5 },
  { from: "Mira (Game Director)", to: "Finn (Level Designer)", weight: 5 },
  { from: "Idris (Brainstorm)", to: "Alex M. (R&D)", weight: 5 },
  { from: "Camille (Marketing)", to: "Sofia (Content)", weight: 5 },
  { from: "Jules (Compta)", to: "Rémi (Contrôle)", weight: 5 },
  { from: "Yuki (Hardware)", to: "Zara (Embedded)", weight: 5 },
  { from: "Layla (Analyste Business)", to: "Axel (Analyste Data)", weight: 5 },
  { from: "Alex O. (QA)", to: "Alex M. (R&D)", weight: 5 },
];

// ─── Per-pôle rich data ─────────────────────────────────────────────────────
export interface PôleBudget { allocated: number; spent: number; currency: string }
export interface Capability { name: string; level: number }
export interface Sensor { label: string; value: string; unit: string; status: "ok" | "warn" | "alert" }
export interface AgentMetric { tasksCompleted: number; avgResponse: string; accuracy: number }
export interface PôleRich {
  budget: PôleBudget;
  capabilities: Capability[];
  sensors: Sensor[];
  performanceTrend: number[];
  agentMetrics: Record<string, AgentMetric>;
}

export const deptRich: Record<string, PôleRich> = {
  ceo: {
    budget: { allocated: 840, spent: 412, currency: "k€" },
    capabilities: [{ name: "Stratégie", level: 96 }, { name: "Vision long terme", level: 92 }, { name: "Arbitrage", level: 88 }, { name: "Leadership", level: 94 }],
    sensors: [{ label: "Décisions / jour", value: "184", unit: "", status: "ok" }, { label: "Alignement pôles", value: "98.4", unit: "%", status: "ok" }, { label: "Vision 5 ans", value: "Active", unit: "", status: "ok" }],
    performanceTrend: [88, 90, 89, 91, 92, 91, 93, 94],
    agentMetrics: { "ceo-1": { tasksCompleted: 184, avgResponse: "1.2s", accuracy: 97 }, "ceo-2": { tasksCompleted: 42, avgResponse: "2.8s", accuracy: 94 } },
  },
  secretariat: {
    budget: { allocated: 180, spent: 92, currency: "k€" },
    capabilities: [{ name: "Coordination", level: 95 }, { name: "Recherche doc.", level: 89 }, { name: "Planification", level: 92 }, { name: "Communication", level: 90 }],
    sensors: [{ label: "Requêtes / jour", value: "1.2k", unit: "", status: "ok" }, { label: "Temps réponse", value: "0.8", unit: "s", status: "ok" }, { label: "File d'attente", value: "3", unit: "", status: "ok" }],
    performanceTrend: [90, 91, 92, 91, 93, 92, 94, 93],
    agentMetrics: { "sec-1": { tasksCompleted: 312, avgResponse: "0.6s", accuracy: 98 }, "sec-2": { tasksCompleted: 248, avgResponse: "0.9s", accuracy: 96 } },
  },
  rd: {
    budget: { allocated: 1260, spent: 718, currency: "k€" },
    capabilities: [{ name: "Recherche fondamentale", level: 93 }, { name: "Prototypage", level: 88 }, { name: "Éthique & alignement", level: 91 }, { name: "Multimodal", level: 85 }],
    sensors: [{ label: "GPU cluster", value: "81", unit: "%", status: "warn" }, { label: "Expériences actives", value: "27", unit: "", status: "ok" }, { label: "Précision modèle", value: "94.2", unit: "%", status: "ok" }],
    performanceTrend: [82, 84, 83, 86, 87, 85, 88, 89],
    agentMetrics: { "rd-1": { tasksCompleted: 56, avgResponse: "4.2s", accuracy: 95 }, "rd-2": { tasksCompleted: 38, avgResponse: "3.1s", accuracy: 97 }, "rd-3": { tasksCompleted: 72, avgResponse: "1.8s", accuracy: 92 } },
  },
  app: {
    budget: { allocated: 940, spent: 524, currency: "k€" },
    capabilities: [{ name: "Frontend", level: 94 }, { name: "Backend / API", level: 91 }, { name: "Mobile", level: 87 }, { name: "DevOps", level: 83 }],
    sensors: [{ label: "Builds / jour", value: "312", unit: "", status: "ok" }, { label: "Coverage tests", value: "94", unit: "%", status: "ok" }, { label: "File CI/CD", value: "2", unit: "", status: "ok" }],
    performanceTrend: [85, 86, 88, 87, 89, 90, 91, 92],
    agentMetrics: { "app-1": { tasksCompleted: 142, avgResponse: "1.4s", accuracy: 96 }, "app-2": { tasksCompleted: 98, avgResponse: "1.6s", accuracy: 94 }, "app-3": { tasksCompleted: 76, avgResponse: "1.2s", accuracy: 93 } },
  },
  gaming: {
    budget: { allocated: 720, spent: 358, currency: "k€" },
    capabilities: [{ name: "Game design", level: 90 }, { name: "Moteur 3D", level: 86 }, { name: "Procédural", level: 84 }, { name: "Narratif", level: 88 }],
    sensors: [{ label: "FPS moyen", value: "144", unit: "fps", status: "ok" }, { label: "Assets générés", value: "12k", unit: "", status: "ok" }, { label: "Mémoire GPU", value: "68", unit: "%", status: "ok" }],
    performanceTrend: [78, 80, 82, 81, 84, 86, 85, 87],
    agentMetrics: { "game-1": { tasksCompleted: 48, avgResponse: "2.1s", accuracy: 93 }, "game-2": { tasksCompleted: 64, avgResponse: "1.5s", accuracy: 95 }, "game-3": { tasksCompleted: 52, avgResponse: "2.4s", accuracy: 91 } },
  },
  robotique: {
    budget: { allocated: 1080, spent: 612, currency: "k€" },
    capabilities: [{ name: "Contrôle moteur", level: 89 }, { name: "SLAM", level: 84 }, { name: "Embarqué", level: 87 }, { name: "Vision robotique", level: 82 }],
    sensors: [{ label: "Temp. moteurs", value: "42.6", unit: "°C", status: "ok" }, { label: "Précision articulaire", value: "0.02", unit: "mm", status: "ok" }, { label: "Batterie NOMAD-1", value: "78", unit: "%", status: "ok" }],
    performanceTrend: [80, 82, 81, 84, 85, 84, 86, 87],
    agentMetrics: { "rob-1": { tasksCompleted: 44, avgResponse: "3.2s", accuracy: 94 }, "rob-2": { tasksCompleted: 58, avgResponse: "1.4s", accuracy: 93 } },
  },
  marketing: {
    budget: { allocated: 560, spent: 348, currency: "k€" },
    capabilities: [{ name: "Growth / SEO", level: 88 }, { name: "Storytelling", level: 92 }, { name: "Social média", level: 90 }, { name: "Analytics", level: 85 }],
    sensors: [{ label: "Reach / mois", value: "4.8M", unit: "", status: "ok" }, { label: "Engagement", value: "7.2", unit: "%", status: "ok" }, { label: "Campagnes live", value: "11", unit: "", status: "ok" }],
    performanceTrend: [84, 86, 85, 88, 90, 89, 91, 92],
    agentMetrics: { "mkt-1": { tasksCompleted: 128, avgResponse: "1.1s", accuracy: 94 }, "mkt-2": { tasksCompleted: 86, avgResponse: "1.8s", accuracy: 96 }, "mkt-3": { tasksCompleted: 164, avgResponse: "0.9s", accuracy: 92 } },
  },
  compta: {
    budget: { allocated: 240, spent: 118, currency: "k€" },
    capabilities: [{ name: "Trésorerie", level: 93 }, { name: "Conformité", level: 96 }, { name: "Reporting", level: 90 }, { name: "Audit", level: 88 }],
    sensors: [{ label: "Transactions / jour", value: "2.4k", unit: "", status: "ok" }, { label: "Trésorerie", value: "Saine", unit: "", status: "ok" }, { label: "Conformité", value: "100", unit: "%", status: "ok" }],
    performanceTrend: [92, 93, 94, 93, 95, 94, 96, 95],
    agentMetrics: { "com-1": { tasksCompleted: 96, avgResponse: "1.2s", accuracy: 99 }, "com-2": { tasksCompleted: 64, avgResponse: "1.5s", accuracy: 98 } },
  },
  connectivite: {
    budget: { allocated: 820, spent: 472, currency: "k€" },
    capabilities: [{ name: "Infrastructure", level: 92 }, { name: "Sécurité", level: 94 }, { name: "Observabilité", level: 90 }, { name: "Edge computing", level: 87 }],
    sensors: [{ label: "Uptime réseau", value: "99.99", unit: "%", status: "ok" }, { label: "Latence US-Ouest", value: "24", unit: "ms", status: "warn" }, { label: "Incid. / mois", value: "0", unit: "", status: "ok" }],
    performanceTrend: [94, 95, 94, 96, 95, 97, 96, 98],
    agentMetrics: { "net-1": { tasksCompleted: 112, avgResponse: "0.8s", accuracy: 97 }, "net-2": { tasksCompleted: 88, avgResponse: "1.0s", accuracy: 98 }, "net-3": { tasksCompleted: 54, avgResponse: "0.7s", accuracy: 95 } },
  },
  direction: {
    budget: { allocated: 460, spent: 214, currency: "k€" },
    capabilities: [{ name: "Operations", level: 91 }, { name: "Programme / OKR", level: 89 }, { name: "Cross-pôles", level: 93 }, { name: "Performance", level: 87 }],
    sensors: [{ label: "Projets actifs", value: "38", unit: "", status: "ok" }, { label: "OKR Q3", value: "71", unit: "%", status: "ok" }, { label: "Throughput", value: "+18", unit: "%", status: "ok" }],
    performanceTrend: [86, 88, 87, 89, 90, 89, 91, 92],
    agentMetrics: { "dir-1": { tasksCompleted: 156, avgResponse: "1.3s", accuracy: 95 }, "dir-2": { tasksCompleted: 98, avgResponse: "1.1s", accuracy: 94 } },
  },
  artistique: {
    budget: { allocated: 480, spent: 296, currency: "k€" },
    capabilities: [{ name: "Direction artistique", level: 95 }, { name: "UI / UX", level: 90 }, { name: "Illustration", level: 88 }, { name: "Motion design", level: 86 }],
    sensors: [{ label: "Assets / sem.", value: "860", unit: "", status: "ok" }, { label: "DA verrouillée", value: "Oui", unit: "", status: "ok" }, { label: "Satisfaction", value: "9.6", unit: "/10", status: "ok" }],
    performanceTrend: [88, 89, 90, 91, 92, 93, 94, 95],
    agentMetrics: { "art-1": { tasksCompleted: 84, avgResponse: "2.2s", accuracy: 96 }, "art-2": { tasksCompleted: 112, avgResponse: "1.7s", accuracy: 94 }, "art-3": { tasksCompleted: 68, avgResponse: "2.5s", accuracy: 92 } },
  },
};

// ─── Global KPIs (extra, for the dashboard strip) ───────────────────────────
export const globalKpis = [
  { label: "Agents actifs", value: "26", delta: "+2", unit: "", trend: [24, 24, 25, 25, 26, 26, 26] },
  { label: "Projets en cours", value: "38", delta: "+5", unit: "", trend: [33, 34, 35, 36, 37, 38, 38] },
  { label: "Décisions / jour", value: "184", delta: "+12", unit: "", trend: [150, 162, 170, 178, 180, 184, 184] },
  { label: "Revenu mensuel", value: "472", delta: "+12%", unit: "k€", trend: [342, 388, 421, 448, 461, 470, 472] },
  { label: "Uptime infra", value: "99.98", delta: "stable", unit: "%", trend: [99.97, 99.98, 99.98, 99.99, 99.98, 99.98, 99.98] },
  { label: "Satisfaction", value: "9.4", delta: "+0.2", unit: "/10", trend: [9.0, 9.1, 9.2, 9.2, 9.3, 9.4, 9.4] },
];
