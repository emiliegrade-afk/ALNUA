export const FINANCES_TABS = [
  "Dashboard",
  "Transactions",
  "Budgets",
  "Prévisions",
  "Facturation",
  "Fiscalité",
  "Salaires",
  "Investissements",
] as const;

export type FinancesTab = (typeof FINANCES_TABS)[number];

export const FINANCES_KPIS = [
  { label: "CASH FLOW", value: "52 480 €", delta: "+10.4%", deltaType: "up" as const, trend: [40, 44, 42, 48, 50, 52], color: "#3DDC97", tab: "Transactions" as FinancesTab },
  { label: "MRR", value: "4 850 €", delta: "+27.6%", deltaType: "up" as const, trend: [3.2, 3.5, 3.8, 4.1, 4.5, 4.85], color: "#3DDC97", tab: "Facturation" as FinancesTab },
  { label: "BURN RATE", value: "420 € / mois", delta: "-5.1%", deltaType: "down" as const, trend: [500, 480, 460, 450, 430, 420], color: "#FF8A4C", tab: "Budgets" as FinancesTab },
  { label: "RUNWAY", value: "97 mois", delta: "Stable", deltaType: "neutral" as const, trend: [90, 92, 93, 94, 95, 97], color: "#60A5FA", tab: "Prévisions" as FinancesTab },
  { label: "PROFIT (MOIS)", value: "18 250 €", delta: "+18.1%", deltaType: "up" as const, trend: [12, 13, 14, 15, 16, 18], color: "#F5C542", tab: "Investissements" as FinancesTab },
  { label: "SOLDE BANCAIRE", value: "62 340 €", delta: "+9.3%", deltaType: "up" as const, trend: [50, 53, 55, 58, 60, 62], color: "#3DDC97", tab: null },
];

export const FINANCES_DEADLINES = [
  { label: "TVA à déclarer", days: 16, amount: "3 240 €" },
  { label: "Factures à payer", days: 7, amount: "1 180 €" },
  { label: "Cotisations sociales", days: 12, amount: "890 €" },
];

export const FINANCES_SUBSCRIPTIONS = [
  { name: "OpenAI", cost: "480 €/mo" },
  { name: "Claude", cost: "220 €/mo" },
  { name: "Cursor IDE", cost: "80 €/mo" },
];

export const FINANCES_BUDGETS = [
  { dept: "APP", budget: 120, spent: 68, href: "/app" },
  { dept: "Gaming", budget: 95, spent: 38, href: "/gaming" },
  { dept: "Robotique", budget: 110, spent: 45, href: "/robo" },
  { dept: "Marketing", budget: 85, spent: 41, href: "/marketing" },
  { dept: "R&D", budget: 126, spent: 72, href: "/rd" },
];

export const FINANCES_TRANSACTIONS = [
  { date: "07/08", desc: "Paiement client NAÏA", amount: 2400, type: "in" as const },
  { date: "06/08", desc: "Facture hosting", amount: -340, type: "out" as const },
  { date: "05/08", desc: "Adspend Meta", amount: -1200, type: "out" as const },
  { date: "04/08", desc: "Prestation NUAWAY", amount: 1800, type: "in" as const },
];

export const FINANCES_INVESTMENTS = [
  { name: "Campagne Ads été", roi: "380%", amount: "4 200 €" },
  { name: "NAÏA V2", roi: "280%", amount: "2 800 €" },
  { name: "Robot Companion", roi: "150%", amount: "6 500 €" },
];
