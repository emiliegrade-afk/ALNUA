"use client";

import { useEffect, useState } from "react";
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

export function SaasInvoicesPanel() {
  const [spend, setSpend] = useState<SaasSpendReport | null>(null);
  const [revolut, setRevolut] = useState<RevolutStatus | null>(null);
  const [invoices, setInvoices] = useState<FinanceInvoice[]>([]);
  const [summary, setSummary] = useState<InvoiceSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [formOpen, setFormOpen] = useState(false);
  const [vendor, setVendor] = useState("");
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
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

  async function handleCreate() {
    const value = parseFloat(amount);
    if (!vendor.trim() || !value || value <= 0) return;
    setSaving(true);
    try {
      await createFinanceInvoice({
        vendor: vendor.trim(),
        amount: value,
        description: description.trim(),
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
            <div
              key={src.id}
              className="rounded-lg border border-copper/10 bg-obsidian-deep/40 p-3"
            >
              <p className="text-[10px] uppercase tracking-wider text-titanium/50">{src.name}</p>
              <p className="mt-1 font-mono text-base text-ivory/90">
                ${Number(src.amount_usd || 0).toFixed(2)}
              </p>
              <p className="text-[11px] text-titanium/45">{src.sync}</p>
            </div>
          ))}
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-lg border border-copper/10 bg-obsidian-deep/40 p-3 text-xs">
            <p className="text-[10px] uppercase tracking-wider text-titanium/50">Revolut</p>
            <p className="mt-1 text-ivory/85">
              {revolut?.configured
                ? `Connecté · ${formatCurrency(revolut.total_eur ?? 0)} (30 j)`
                : "Non configuré — lecture seule quand REVOLUT_ACCESS_TOKEN est posé"}
            </p>
            {revolut?.reason ? (
              <p className="mt-1 text-titanium/45">{revolut.reason}</p>
            ) : null}
          </div>
          <div className="rounded-lg border border-copper/10 bg-obsidian-deep/40 p-3 text-xs">
            <p className="text-[10px] uppercase tracking-wider text-titanium/50">Gmail ops</p>
            <p className="mt-1 text-ivory/85">
              {gmail?.ok
                ? `OK · ${gmail.profile ?? gmail.expected}`
                : `Attendu ${gmail?.expected ?? "alnua.global@gmail.com"} · connecté=${String(gmail?.connected ?? false)}`}
            </p>
          </div>
        </div>

        {tools.length > 0 ? (
          <ul className="max-h-40 space-y-1 overflow-y-auto">
            {tools.slice(0, 12).map((t) => (
              <li
                key={t.name}
                className="flex items-center justify-between gap-2 rounded-lg bg-obsidian-deep/40 px-3 py-1.5 text-xs"
              >
                <span className="text-ivory/80">
                  {t.name}
                  <span className="text-titanium/40">
                    {" "}
                    · {t.plan || "—"} · {t.sync}
                  </span>
                </span>
                <span className="font-mono text-titanium/70">
                  {t.monthly_usd != null ? `$${t.monthly_usd}/mois` : "usage"}
                </span>
              </li>
            ))}
          </ul>
        ) : null}
      </section>

      <section className="space-y-3 rounded-xl border border-copper/10 bg-obsidian-2/40 p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-medium text-ivory">Factures (suivi)</h2>
            <p className="text-[11px] text-titanium/45">
              {summary?.payment_policy ?? "Paiement externe uniquement — les agents ne paient pas."}
            </p>
          </div>
          <div className="text-right text-xs text-titanium/60">
            À payer :{" "}
            <span className="font-mono text-copper">
              {formatCurrency(summary?.to_pay_total ?? 0)} ({summary?.to_pay_count ?? 0})
            </span>
          </div>
        </div>

        <ul className="space-y-1">
          {invoices.slice(0, 20).map((inv) => (
            <li
              key={inv.id}
              className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-obsidian-deep/40 px-3 py-2 text-xs"
            >
              <div>
                <p className="text-ivory/85">
                  {inv.vendor}{" "}
                  <span className="text-titanium/40">· {STATUS_LABEL[inv.status] ?? inv.status}</span>
                </p>
                <p className="text-titanium/45">
                  {inv.description || "—"} · échéance {inv.due_date}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-ivory/80">
                  {formatCurrency(inv.amount, inv.currency)}
                </span>
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
          ))}
          {invoices.length === 0 ? (
            <li className="text-xs text-titanium/50">Aucune facture enregistrée.</li>
          ) : null}
        </ul>

        {formOpen ? (
          <div className="space-y-2 rounded-lg border border-copper/15 bg-obsidian/60 p-3">
            <div className="grid gap-2 sm:grid-cols-2">
              <input
                value={vendor}
                onChange={(e) => setVendor(e.target.value)}
                placeholder="Fournisseur"
                className="rounded-lg border border-copper/15 bg-obsidian px-3 py-1.5 text-sm text-ivory outline-none placeholder:text-titanium/40"
              />
              <input
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                type="number"
                step="0.01"
                placeholder="Montant EUR"
                className="rounded-lg border border-copper/15 bg-obsidian px-3 py-1.5 text-sm text-ivory outline-none placeholder:text-titanium/40"
              />
            </div>
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Description"
              className="w-full rounded-lg border border-copper/15 bg-obsidian px-3 py-1.5 text-sm text-ivory outline-none placeholder:text-titanium/40"
            />
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setFormOpen(false)}
                className="rounded-lg px-3 py-1.5 text-xs text-titanium/60 hover:text-ivory"
              >
                Annuler
              </button>
              <button
                type="button"
                onClick={() => void handleCreate()}
                disabled={saving || !vendor.trim() || !amount}
                className="rounded-lg bg-copper px-3 py-1.5 text-xs font-medium text-obsidian hover:bg-copper/90 disabled:opacity-50"
              >
                {saving ? <Loader2 className="inline h-3 w-3 animate-spin" /> : null} Ajouter
              </button>
            </div>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setFormOpen(true)}
            className="flex items-center gap-1.5 text-xs text-titanium/60 hover:text-copper"
          >
            <Plus className="h-3.5 w-3.5" />
            Ajouter une facture à suivre
          </button>
        )}
      </section>
    </div>
  );
}
