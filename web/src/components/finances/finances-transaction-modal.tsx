"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import {
  categoriesForType,
  CATEGORY_LABELS,
  RECURRENCE_LABELS,
} from "@/components/finances/finances.constants";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import {
  createFinanceTransaction,
  updateFinanceTransaction,
  type FinanceTransaction,
  type FinanceTransactionInput,
  type Recurrence,
  type TransactionType,
} from "@/lib/finances-api";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";

interface FinancesTransactionModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projects: Project[];
  transaction?: FinanceTransaction | null;
  defaultMonth?: string;
  onSaved: () => void;
}

export function FinancesTransactionModal({
  open,
  onOpenChange,
  projects,
  transaction,
  defaultMonth,
  onSaved,
}: FinancesTransactionModalProps) {
  const isEdit = Boolean(transaction);

  const [txType, setTxType] = useState<TransactionType>("expense");
  const [amount, setAmount] = useState("");
  const [currency, setCurrency] = useState("EUR");
  const [txDate, setTxDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [category, setCategory] = useState("");
  const [projectId, setProjectId] = useState<string>("none");
  const [description, setDescription] = useState("");
  const [isRecurring, setIsRecurring] = useState(false);
  const [recurrence, setRecurrence] = useState<Recurrence>("monthly");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!open) return;

    if (transaction) {
      setTxType(transaction.type);
      setAmount(String(transaction.amount));
      setCurrency(transaction.currency);
      setTxDate(transaction.date.slice(0, 10));
      setCategory(transaction.category);
      setProjectId(transaction.project_id ?? "none");
      setDescription(transaction.description ?? "");
      setIsRecurring(transaction.is_recurring);
      setRecurrence(transaction.recurrence ?? "monthly");
    } else {
      setTxType("expense");
      setAmount("");
      setCurrency("EUR");
      const defaultDate = defaultMonth
        ? `${defaultMonth}-01`
        : new Date().toISOString().slice(0, 10);
      setTxDate(defaultDate);
      const cats = categoriesForType("expense");
      setCategory(cats[0] ?? "autre");
      setProjectId("none");
      setDescription("");
      setIsRecurring(false);
      setRecurrence("monthly");
    }
  }, [open, transaction, defaultMonth]);

  useEffect(() => {
    if (!open || isEdit) return;
    const cats = categoriesForType(txType);
    if (!cats.includes(category as never)) {
      setCategory(cats[0] ?? "autre");
    }
  }, [txType, open, isEdit, category]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const num = parseFloat(amount.replace(",", "."));
    if (Number.isNaN(num) || num <= 0) {
      toast.error("Montant invalide");
      return;
    }
    if (!category) {
      toast.error("Choisis une catégorie");
      return;
    }

    const payload: FinanceTransactionInput = {
      date: txDate,
      type: txType,
      amount: num,
      currency,
      category,
      project_id: projectId === "none" ? null : projectId,
      description: description.trim() || null,
      is_recurring: isRecurring,
      recurrence: isRecurring ? recurrence : null,
    };

    setSubmitting(true);
    try {
      if (transaction) {
        await updateFinanceTransaction(transaction.id, payload);
        toast.success("Transaction mise à jour");
      } else {
        await createFinanceTransaction(payload);
        toast.success("Transaction enregistrée");
      }
      onSaved();
      onOpenChange(false);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur");
    } finally {
      setSubmitting(false);
    }
  }

  const cats = categoriesForType(txType);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto border-white/10 bg-surface sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-ivory">
            {isEdit ? "Modifier la transaction" : "Ajouter une transaction"}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="flex rounded-lg border border-white/10 p-1">
            <button
              type="button"
              className={cn(
                "flex-1 rounded-md py-2 text-sm font-medium transition",
                txType === "income"
                  ? "bg-emerald-500/20 text-emerald-300"
                  : "text-titanium hover:text-ivory"
              )}
              onClick={() => setTxType("income")}
            >
              Revenu
            </button>
            <button
              type="button"
              className={cn(
                "flex-1 rounded-md py-2 text-sm font-medium transition",
                txType === "expense"
                  ? "bg-red-500/20 text-red-300"
                  : "text-titanium hover:text-ivory"
              )}
              onClick={() => setTxType("expense")}
            >
              Dépense
            </button>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label htmlFor="amount">Montant</Label>
              <Input
                id="amount"
                type="text"
                inputMode="decimal"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="49.00"
                required
                className="border-white/10 bg-black/20"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="currency">Devise</Label>
              <Select value={currency} onValueChange={setCurrency}>
                <SelectTrigger id="currency" className="border-white/10 bg-black/20">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="EUR">EUR</SelectItem>
                  <SelectItem value="USD">USD</SelectItem>
                  <SelectItem value="GBP">GBP</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="tx-date">Date</Label>
            <Input
              id="tx-date"
              type="date"
              value={txDate}
              onChange={(e) => setTxDate(e.target.value)}
              required
              className="border-white/10 bg-black/20"
            />
          </div>

          <div className="space-y-2">
            <Label>Catégorie</Label>
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger className="border-white/10 bg-black/20">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {cats.map((cat) => (
                  <SelectItem key={cat} value={cat}>
                    {CATEGORY_LABELS[cat] ?? cat}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Projet (optionnel)</Label>
            <Select value={projectId} onValueChange={setProjectId}>
              <SelectTrigger className="border-white/10 bg-black/20">
                <SelectValue placeholder="ALNUA global" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">ALNUA global</SelectItem>
                {projects.map((p) => (
                  <SelectItem key={p.id} value={p.id}>
                    {p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Ex. Abonnement Figma"
              rows={2}
              className="border-white/10 bg-black/20"
            />
          </div>

          <div className="space-y-3 rounded-lg border border-white/10 p-3">
            <label className="flex cursor-pointer items-center gap-2 text-sm text-ivory">
              <input
                type="checkbox"
                checked={isRecurring}
                onChange={(e) => setIsRecurring(e.target.checked)}
                className="rounded border-white/20"
              />
              Transaction récurrente
            </label>
            {isRecurring ? (
              <Select
                value={recurrence}
                onValueChange={(v) => setRecurrence(v as Recurrence)}
              >
                <SelectTrigger className="border-white/10 bg-black/20">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {(Object.keys(RECURRENCE_LABELS) as Recurrence[]).map((r) => (
                    <SelectItem key={r} value={r}>
                      {RECURRENCE_LABELS[r]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : null}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="ghost"
              onClick={() => onOpenChange(false)}
            >
              Annuler
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Enregistrement…" : "Enregistrer"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
