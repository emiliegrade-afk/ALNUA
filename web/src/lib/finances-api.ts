import { hubApiKeyHeaders } from "./hub-api-key";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  "http://localhost:8000";

async function apiFetch<T>(
  path: string,
  options?: RequestInit & { timeoutMs?: number }
): Promise<T> {
  const { timeoutMs = 30_000, ...fetchOptions } = options ?? {};
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${API_URL}${path}`, {
      ...fetchOptions,
      signal: controller.signal,
      headers: hubApiKeyHeaders({
        "Content-Type": "application/json",
        ...fetchOptions.headers,
      }),
      cache: "no-store",
    });

    if (!res.ok) {
      const text = await res.text().catch(() => res.statusText);
      try {
        const json = JSON.parse(text) as { detail?: string };
        if (json.detail) throw new Error(json.detail);
      } catch (e) {
        if (e instanceof Error && e.message !== text) throw e;
      }
      throw new Error(`API ${res.status}: ${text}`);
    }

    if (res.status === 204) return undefined as T;
    return res.json() as Promise<T>;
  } catch (err) {
    if (err instanceof Error && err.name === "AbortError") {
      throw new Error("API timeout — le serveur met trop de temps à répondre.");
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

export type TransactionType = "income" | "expense";

export type ExpenseCategory =
  | "saas_tools"
  | "hardware"
  | "freelance"
  | "marketing"
  | "legal"
  | "hosting"
  | "formation"
  | "autre";

export type IncomeCategory =
  | "app_revenue"
  | "grant"
  | "consulting"
  | "investment"
  | "autre";

export type TransactionCategory = ExpenseCategory | IncomeCategory;

export type Recurrence = "monthly" | "annual" | "one_time";

export interface FinanceTransaction {
  id: string;
  date: string;
  type: TransactionType;
  amount: number;
  currency: string;
  category: TransactionCategory | string;
  project_id: string | null;
  project_name?: string;
  description: string | null;
  is_recurring: boolean;
  recurrence: Recurrence | null;
  receipt_url: string | null;
  created_at: string;
}

export interface FinancialSummary {
  id: string;
  month: string;
  summary_md: string | null;
  total_income: number;
  total_expenses: number;
  balance: number;
  by_category: Record<string, number>;
  created_at: string;
}

export interface MonthTotals {
  month: string;
  total_income: number;
  total_expenses: number;
  balance: number;
  by_category?: Record<string, number>;
  recurring_count?: number;
}

export interface FinanceDashboard {
  current_month: MonthTotals;
  last_3_months: MonthTotals[];
  last_6_months: MonthTotals[];
  recurring_expenses: FinanceTransaction[];
  ytd_balance: number;
}

export interface FinanceTransactionInput {
  date: string;
  type: TransactionType;
  amount: number;
  currency?: string;
  category: string;
  project_id?: string | null;
  description?: string | null;
  is_recurring?: boolean;
  recurrence?: Recurrence | null;
}

function qs(params: Record<string, string | undefined>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v) sp.set(k, v);
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

export function fetchFinanceTransactions(filters?: {
  month?: string;
  type?: TransactionType;
  category?: string;
  project_id?: string;
}): Promise<FinanceTransaction[]> {
  return apiFetch(
    `/finances/transactions${qs({
      month: filters?.month,
      type: filters?.type,
      category: filters?.category,
      project_id: filters?.project_id,
    })}`
  );
}

export function createFinanceTransaction(
  body: FinanceTransactionInput
): Promise<FinanceTransaction> {
  return apiFetch("/finances/transactions", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function updateFinanceTransaction(
  id: string,
  body: Partial<FinanceTransactionInput>
): Promise<FinanceTransaction> {
  return apiFetch(`/finances/transactions/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export function deleteFinanceTransaction(id: string): Promise<{ ok: boolean }> {
  return apiFetch(`/finances/transactions/${id}`, { method: "DELETE" });
}

export function fetchFinanceSummary(month: string): Promise<FinancialSummary> {
  return apiFetch(`/finances/summary/${month}`, { timeoutMs: 90_000 });
}

export function regenerateFinanceSummary(month: string): Promise<FinancialSummary> {
  return apiFetch("/finances/summary/generate", {
    method: "POST",
    body: JSON.stringify({ month }),
    timeoutMs: 90_000,
  });
}

export function fetchFinanceDashboard(month?: string): Promise<FinanceDashboard> {
  return apiFetch(
    `/finances/dashboard${qs({ month })}`
  );
}

export function formatCurrency(amount: number, currency = "EUR"): string {
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(amount);
}

export function currentMonthKey(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

export function shiftMonth(month: string, delta: number): string {
  const [y, m] = month.split("-").map(Number);
  const d = new Date(y, m - 1 + delta, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}
