"use client";

import { useEffect, useMemo, useState } from "react";
import { Loader2, Plus } from "lucide-react";
import { toast } from "sonner";
import {
  createFinanceInvoice,
  fetchFinanceInvoices,
  fetchRevolutStatus,
  fetchSaasSpend,
  formatCurrency,
  updateFinanceInvoice,
  type FinanceInvoice,
  type InvoiceStatus,
  type InvoiceSummary,
  type RevolutStatus,
  type SaasSpendReport,
} from "@/lib/finances-api";

const STATUS_LABEL: Record<InvoiceStatus, string> = {
  draft: "Brouillon",
  received: "Reçue",
  to_pay: "À payer",
  paid_externally: "Payée (externe)",
  cancelled: "Annulée",
};

type InvoiceTab = "to_pay" | "paid" | "all";

function isOverdue(inv: FinanceInvoice): boolean {
  if (inv.status !== "to_pay" && inv.status !== "received") return false;
  return inv.due_date.slice(0, 10) < new Date().toISOString().slice(0, 10);
}

function filterInvoices(invoices: FinanceInvoice[], tab: InvoiceTab): FinanceInvoice[] {
  let rows = invoices;
  if (tab === "to_pay") {
    rows = rows.filter((i) => i.status === "to_pay" || i.status === "received");
    return [...rows].sort((a, b) => a.due_date.localeCompare(b.due_date));
  }
  if (tab === "paid") {
    return rows.filter((i) => i.status === "paid_externally");
  }
  return rows;
}

export function SaasInvoicesPanel() {
  const [spend, setSpend] = useState<SaasSpendReport | null>(null);
  const [revolut, setRevolut] = useState<RevolutStatus | null>(null);
  const [invoices, setInvoices] = useState<FinanceInvoice[]>([]);
  const [summary, setSummary] = useState<InvoiceSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [formOpen, setFormOpen] = useState(false);
  const [invoiceTab, setInvoiceTab] = useState<InvoiceTab>("to_pay");
  const [vendor, setVendor] = useState("");
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [dueDate, setDueDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const [s, inv, rev] = await Promise.all([
        fetchSaasSpend(30),
        fetchFinanceInvoices(),
        fetchRevolutStatus(30),
      ]);
      setSpend(s);
      setInvoices(inv.invoices);
      setSummary(inv.summary);
      setRevolut(rev);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Chargement finances impossible");
      setSpend(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const visibleInvoices = useMemo(
    () => filterInvoices(invoices, invoiceTab),
    [invoices, invoiceTab],
  );

  async function handleCreate() {
    const value = parseFloat(amount);
    if (!vendor.trim() || !value || value <= 0) return;
    setSaving(true);
    try {
      await createFinanceInvoice({
        vendor: vendor.trim(),
        amount: value,
        description: description.trim(),
        due_date: dueDate || undefined,
        status: "to_pay",
        category: "saas_tools",
      });
      toast.success("Facture ajoutée (paiement hors Hub).");
      setVendor("");
      setAmount("");
      setDescription("");
      setFormOpen(false);
      await load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    } finally {
      setSaving(false);
    }
  }

  async function markPaid(id: string) {
    try {
      await updateFinanceInvoice(id, { status: "paid_externally" });
      toast.success("Marquée payée en externe.");
      await load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    }
  }

  if (loading && !spend) {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-copper/10 bg-obsidian-2/40 p-4 text-sm text-titanium/60">
        <Loader2 className="h-4 w-4 animate-spin" />
        Chargement abonnements & factures…
      </div>
    );
  }

  const tools = spend?.catalog?.tools ?? [];
  const gmail = spend?.gmail_ops;
  const tabBtn = (tab: InvoiceTab, label: string) => (
    <button
      type="button"
      onClick={() => setInvoiceTab(tab)}
      className={`rounded-md px-2 py-1 text-[10px] ${
        invoiceTab === tab
          ? "bg-copper/15 text-copper"
          : "text-titanium/50 hover:text-titanium/80"
      }`}
    >
      {label}
    </button>
  );

  return (
    <div className="space-y-4">
      <section className="space-y-3 rounded-xl border border-copper/10 bg-obsidian-2/40 p-4">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-sm font-medium text-ivory">Abonnements & sync — 30 j</h2>
          <span className="font-mono text-lg font-semibold text-copper">
            ${spend?.total_tracked_usd?.toFixed(2) ?? "—"}
          </span>
        </div>
        <p className="text-[11px] text-titanium/45">{spend?.currency_note}</p>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {(spend?.sources ?? []).map((src) => (
            <div key={src.id} className="rounded-lg border border-copper/10 bg-obsidian-deep/40 p-3">
              <p className="text-[10px] uppercase tracking-wider text-titanium/50">{src.name}</p>
              <p className="mt-1 font-mono text-base text-ivory/90">${Number(src.amount_usd || 0).toFixed(2)}</p>
              <p className="text-[11px] text-titanium/45">{src.sync}</p>
            </div>
          ))}
        </div>
        {tools.length > 0 ? (
          <ul className="max-h-32 space-y-1 overflow-y-auto">
            {tools.slice(0, 8).map((t) => (
              <li key={t.name} className="flex justify-between rounded-lg bg-obsidian-deep/40 px-3 py-1 text-xs text-ivory/80">
                <span>{t.name}</span>
                <span className="font-mono text-titanium/70">
                  {t.monthly_usd != null ? `$${t.monthly_usd}/mois` : "usage"}
                </span>
              </li>
            ))}
          </ul>
        ) : null}
      </section>

      <section className="space-y-3 rounded-xl border border-copper/10 bg-obsidian-2/40 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-medium text-ivory">Factures (suivi)</h2>
            <p className="text-[11px] text-titanium/45">
              {summary?.payment_policy ?? "Paiement externe uniquement."}
            </p>
          </div>
          <div className="flex gap-1">
            {tabBtn("to_pay", "À payer")}
            {tabBtn("paid", "Payées")}
            {tabBtn("all", "Toutes")}
          </div>
        </div>
        <p className="text-xs text-titanium/60">
          À payer :{" "}
          <span className="font-mono text-copper">
            {formatCurrency(summary?.to_pay_total ?? 0)} ({summary?.to_pay_count ?? 0})
          </span>
        </p>

        <ul className="space-y-1">
          {visibleInvoices.slice(0, 25).map((inv) => {
            const overdue = isOverdue(inv);
            return (
              <li
                key={inv.id}
                className={`flex flex-wrap items-center justify-between gap-2 rounded-lg px-3 py-2 text-xs ${
                  overdue ? "border border-danger/30 bg-danger/5" : "bg-obsidian-deep/40"
                }`}
              >
                <div>
                  <p className="text-ivory/85">
                    {inv.vendor}{" "}
                    <span className="text-titanium/40">· {STATUS_LABEL[inv.status] ?? inv.status}</span>
                    {overdue ? <span className="ml-1 text-danger">· en retard</span> : null}
                  </p>
                  <p className="text-titanium/45">
                    {inv.description || "—"} · échéance {inv.due_date.slice(0, 10)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-ivory/80">{formatCurrency(inv.amount, inv.currency)}</span>
                  {inv.status === "to_pay" || inv.status === "received" ? (
                    <button
                      type="button"
                      onClick={() => void markPaid(inv.id)}
                      className="rounded-md border border-copper/20 px-2 py-1 text-[10px] text-copper hover:bg-copper/10"
                    >
                      Payée hors Hub
                    </button>
                  ) : null}
                </div>
              </li>
            );
          })}
          {visibleInvoices.length === 0 ? (
            <li className="text-xs text-titanium/50">Aucune facture dans cet onglet.</li>
          ) : null}
        </ul>

        {formOpen ? (
          <div className="space-y-2 rounded-lg border border-copper/15 bg-obsidian/60 p-3">
            <div className="grid gap-2 sm:grid-cols-3">
              <input value={vendor} onChange={(e) => setVendor(e.target.value)} placeholder="Fournisseur" className="rounded-lg border border-copper/15 bg-obsidian px-3 py-1.5 text-sm text-ivory outline-none" />
              <input value={amount} onChange={(e) => setAmount(e.target.value)} type="number" step="0.01" placeholder="Montant EUR" className="rounded-lg border border-copper/15 bg-obsidian px-3 py-1.5 text-sm text-ivory outline-none" />
              <input value={dueDate} onChange={(e) => setDueDate(e.target.value)} type="date" className="rounded-lg border border-copper/15 bg-obsidian px-3 py-1.5 text-sm text-ivory outline-none" />
            </div>
            <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description" className="w-full rounded-lg border border-copper/15 bg-obsidian px-3 py-1.5 text-sm text-ivory outline-none" />
            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => setFormOpen(false)} className="rounded-lg px-3 py-1.5 text-xs text-titanium/60">Annuler</button>
              <button type="button" onClick={() => void handleCreate()} disabled={saving || !vendor.trim() || !amount} className="rounded-lg bg-copper px-3 py-1.5 text-xs font-medium text-obsidian disabled:opacity-50">
                {saving ? <Loader2 className="inline h-3 w-3 animate-spin" /> : null} Ajouter
              </button>
            </div>
          </div>
        ) : (
          <button type="button" onClick={() => setFormOpen(true)} className="flex items-center gap-1.5 text-xs text-titanium/60 hover:text-copper">
            <Plus className="h-3.5 w-3.5" /> Ajouter une facture à suivre
          </button>
        )}
      </section>
    </div>
  );
}
