import type { ExpenseCategory, IncomeCategory, Recurrence } from "@/lib/finances-api";

export const EXPENSE_CATEGORIES: ExpenseCategory[] = [
  "saas_tools",
  "hardware",
  "freelance",
  "marketing",
  "legal",
  "hosting",
  "formation",
  "autre",
];

export const INCOME_CATEGORIES: IncomeCategory[] = [
  "app_revenue",
  "grant",
  "consulting",
  "investment",
  "autre",
];

export const CATEGORY_LABELS: Record<string, string> = {
  saas_tools: "Outils SaaS",
  hardware: "Matériel",
  freelance: "Freelance",
  marketing: "Marketing",
  legal: "Juridique",
  hosting: "Hébergement",
  formation: "Formation",
  autre: "Autre",
  app_revenue: "Revenus app",
  grant: "Subvention",
  consulting: "Consulting",
  investment: "Investissement",
};

export const EXPENSE_CATEGORY_COLORS: Record<ExpenseCategory, string> = {
  saas_tools: "#6366f1",
  hardware: "#8b5cf6",
  freelance: "#ec4899",
  marketing: "#f97316",
  legal: "#64748b",
  hosting: "#06b6d4",
  formation: "#eab308",
  autre: "#94a3b8",
};

export const RECURRENCE_LABELS: Record<Recurrence, string> = {
  monthly: "Mensuel",
  annual: "Annuel",
  one_time: "Ponctuel",
};

export function categoriesForType(type: "income" | "expense"): string[] {
  return type === "income" ? INCOME_CATEGORIES : EXPENSE_CATEGORIES;
}

export function formatMonthLabel(month: string): string {
  const [y, m] = month.split("-").map(Number);
  return new Intl.DateTimeFormat("fr-FR", {
    month: "short",
    year: "2-digit",
  }).format(new Date(y, m - 1, 1));
}

export function formatMonthTitle(month: string): string {
  const [y, m] = month.split("-").map(Number);
  return new Intl.DateTimeFormat("fr-FR", {
    month: "long",
    year: "numeric",
  }).format(new Date(y, m - 1, 1));
}
