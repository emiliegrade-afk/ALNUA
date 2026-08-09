export const APP_TEAM_IDS = ["theo", "hao", "ines", "rayan", "sam"] as const;
export type AppTeamId = (typeof APP_TEAM_IDS)[number];

export const APP_TEAM_LOADS: Record<AppTeamId, { disponibility: number; charge: number; tasks: number }> = {
  theo: { disponibility: 72, charge: 68, tasks: 31 },
  hao: { disponibility: 64, charge: 82, tasks: 24 },
  ines: { disponibility: 80, charge: 65, tasks: 18 },
  rayan: { disponibility: 70, charge: 71, tasks: 15 },
  sam: { disponibility: 85, charge: 58, tasks: 22 },
};

export const APP_TEAM_SKILLS: Record<AppTeamId, { name: string; pct: number }[]> = {
  theo: [
    { name: "React Native", pct: 96 },
    { name: "TypeScript", pct: 94 },
    { name: "Expo", pct: 91 },
    { name: "Notifications", pct: 88 },
    { name: "Deep linking", pct: 82 },
  ],
  hao: [
    { name: "Node / FastAPI", pct: 95 },
    { name: "Postgres", pct: 92 },
    { name: "API design", pct: 90 },
    { name: "Auth", pct: 86 },
    { name: "Perf SQL", pct: 80 },
  ],
  ines: [
    { name: "Figma", pct: 97 },
    { name: "Design system", pct: 93 },
    { name: "Proto", pct: 90 },
    { name: "Motion", pct: 78 },
    { name: "Accessibilité", pct: 84 },
  ],
  rayan: [
    { name: "CI/CD", pct: 94 },
    { name: "Docker", pct: 90 },
    { name: "GitHub Actions", pct: 88 },
    { name: "Observabilité", pct: 76 },
    { name: "Infra", pct: 82 },
  ],
  sam: [
    { name: "Roadmap", pct: 93 },
    { name: "Specs", pct: 91 },
    { name: "Priorisation", pct: 89 },
    { name: "Stakeholders", pct: 86 },
    { name: "Delivery", pct: 84 },
  ],
};

export const APP_TEAM_MISSIONS: Record<AppTeamId, { current: string; next: string; progress: number }> = {
  theo: { current: "Notifications Push", next: "Intégration DeepLink", progress: 78 },
  hao: { current: "API Hydratation", next: "Database Migration", progress: 63 },
  ines: { current: "UI Kit v2.4", next: "Dashboard Nutrition", progress: 92 },
  rayan: { current: "Pipeline CI Hub", next: "Store build v2.4", progress: 70 },
  sam: { current: "Sprint 19 NAÏA", next: "Review backlog Q3", progress: 55 },
};

export const APP_TEAM_ACTIVITY: Record<AppTeamId, { text: string; time: string }[]> = {
  theo: [
    { text: "a pushé NotificationsService.ts", time: "22:14" },
    { text: "a mis à jour MessageList · Academy", time: "21:48" },
    { text: "a commenté DeepLink spec", time: "20:12" },
  ],
  hao: [
    { text: "a déployé API v2 · NAÏA", time: "22:03" },
    { text: "a merge Auth refactor", time: "21:10" },
  ],
  ines: [
    { text: "a partagé maquette Hub", time: "21:55" },
    { text: "attend validation UI Kit", time: "20:40" },
  ],
  rayan: [
    { text: "a mergé pipeline CI · Hub", time: "21:42" },
    { text: "a fixé build Android", time: "19:58" },
  ],
  sam: [
    { text: "a priorisé Sprint 19 · NAÏA", time: "21:30" },
    { text: "a validé critères Push", time: "18:20" },
  ],
};

export const APP_TEAM_STATS: Record<AppTeamId, [string, string][]> = {
  theo: [
    ["48", "Missions terminées"],
    ["94%", "Qualité du code"],
    ["92%", "Respect délais"],
    ["98%", "Collaboration"],
  ],
  hao: [
    ["52", "Missions terminées"],
    ["96%", "Qualité du code"],
    ["88%", "Respect délais"],
    ["95%", "Collaboration"],
  ],
  ines: [
    ["41", "Missions terminées"],
    ["97%", "Qualité design"],
    ["90%", "Respect délais"],
    ["99%", "Collaboration"],
  ],
  rayan: [
    ["36", "Missions terminées"],
    ["93%", "Stabilité builds"],
    ["91%", "Respect délais"],
    ["94%", "Collaboration"],
  ],
  sam: [
    ["29", "Missions terminées"],
    ["90%", "Qualité specs"],
    ["95%", "Respect délais"],
    ["97%", "Collaboration"],
  ],
};

export const APP_TEAM_RADAR = [
  { label: "Code", value: 92 },
  { label: "Résolution", value: 88 },
  { label: "Créativité", value: 74 },
  { label: "Connexion", value: 96 },
  { label: "Autonomie", value: 90 },
];
