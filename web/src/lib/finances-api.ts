import { hubFetch } from "./hub-fetch";

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
  // Rattache une dépense à une campagne (Phase 33, ROADMAP.md) — permet de
  // calculer un "dépensé réel" par campagne côté GET /campaigns.
  campaign_id: string | null;
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
  campaign_id?: string | null;
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
  return hubFetch(
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
  return hubFetch("/finances/transactions", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function updateFinanceTransaction(
  id: string,
  body: Partial<FinanceTransactionInput>
): Promise<FinanceTransaction> {
  return hubFetch(`/finances/transactions/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export function deleteFinanceTransaction(id: string): Promise<{ ok: boolean }> {
  return hubFetch(`/finances/transactions/${id}`, { method: "DELETE" });
}

export function fetchFinanceSummary(month: string): Promise<FinancialSummary> {
  return hubFetch(`/finances/summary/${month}`, { timeoutMs: 90_000 });
}

export function regenerateFinanceSummary(month: string): Promise<FinancialSummary> {
  return hubFetch("/finances/summary/generate", {
    method: "POST",
    body: JSON.stringify({ month }),
    timeoutMs: 90_000,
  });
}

export function fetchFinanceDashboard(month?: string): Promise<FinanceDashboard> {
  return hubFetch(
    `/finances/dashboard${qs({ month })}`
  );
}

export type InvoiceStatus =
  | "draft"
  | "received"
  | "to_pay"
  | "paid_externally"
  | "cancelled";

export interface FinanceInvoice {
  id: string;
  vendor: string;
  amount: number;
  currency: string;
  description: string;
  due_date: string;
  category: string;
  receipt_url: string;
  external_ref: string;
  status: InvoiceStatus;
  paid_at?: string | null;
  created_at: string;
  updated_at?: string;
  notes?: string;
}

export interface InvoiceSummary {
  count: number;
  by_status_amount: Record<string, number>;
  to_pay_count: number;
  to_pay_total: number;
  payment_policy: string;
}

export interface SaasSpendSource {
  id: string;
  name: string;
  sync: string;
  amount_usd: number;
  detail?: Record<string, unknown>;
}

export interface SaasSpendReport {
  as_of: string;
  days: number;
  currency_note: string;
  total_tracked_usd: number;
  sources: SaasSpendSource[];
  catalog?: {
    tools?: Array<{
      name: string;
      sync?: string;
      monthly_usd?: number | null;
      plan?: string;
      category?: string;
    }>;
  };
  gmail_ops?: {
    connected?: boolean;
    expected?: string;
    profile?: string | null;
    ok?: boolean;
  };
}

export interface RevolutStatus {
  configured: boolean;
  expenses?: unknown[];
  total_eur?: number;
  reason?: string;
  message?: string;
  status?: string;
}

export function fetchSaasSpend(days = 30): Promise<SaasSpendReport> {
  return hubFetch(`/finances/saas-spend?days=${days}`);
}

export function fetchFinanceInvoices(filters?: {
  status?: InvoiceStatus;
  vendor?: string;
}): Promise<{ invoices: FinanceInvoice[]; summary: InvoiceSummary }> {
  return hubFetch(
    `/finances/invoices${qs({
      status: filters?.status,
      vendor: filters?.vendor,
    })}`
  );
}

export function createFinanceInvoice(body: {
  vendor: string;
  amount: number;
  currency?: string;
  description?: string;
  due_date?: string;
  category?: string;
  status?: InvoiceStatus;
}): Promise<FinanceInvoice> {
  return hubFetch("/finances/invoices", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function updateFinanceInvoice(
  id: string,
  body: Partial<{
    vendor: string;
    amount: number;
    description: string;
    due_date: string;
    category: string;
    status: InvoiceStatus;
    notes: string;
  }>
): Promise<FinanceInvoice> {
  return hubFetch(`/finances/invoices/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export function fetchRevolutStatus(days = 30): Promise<RevolutStatus> {
  return hubFetch(`/finances/revolut/status?days=${days}`);
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
