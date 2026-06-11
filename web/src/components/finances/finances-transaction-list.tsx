"use client";

import { useEffect, useState } from "react";
import { format, parseISO } from "date-fns";
import { fr } from "date-fns/locale";
import {
  Cloud,
  Cpu,
  GraduationCap,
  Landmark,
  Megaphone,
  MoreHorizontal,
  Pencil,
  Repeat,
  Scale,
  Server,
  Trash2,
  TrendingUp,
  Users,
  Wallet,
} from "lucide-react";
import { toast } from "sonner";
import {
  CATEGORY_LABELS,
  categoriesForType,
} from "@/components/finances/finances.constants";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  deleteFinanceTransaction,
  formatCurrency,
  type FinanceTransaction,
  type TransactionType,
} from "@/lib/finances-api";
import { cn } from "@/lib/utils";

const CATEGORY_ICONS: Record<string, typeof Wallet> = {
  saas_tools: Cloud,
  hardware: Cpu,
  freelance: Users,
  marketing: Megaphone,
  legal: Scale,
  hosting: Server,
  formation: GraduationCap,
  app_revenue: TrendingUp,
  grant: Landmark,
  consulting: Users,
  investment: Wallet,
  autre: MoreHorizontal,
};

interface FinancesTransactionListProps {
  transactions: FinanceTransaction[];
  typeFilter: "all" | TransactionType;
  categoryFilter: string;
  onTypeFilterChange: (v: "all" | TransactionType) => void;
  onCategoryFilterChange: (v: string) => void;
  onEdit: (tx: FinanceTransaction) => void;
  onDeleted: () => void;
}

export function FinancesTransactionList({
  transactions,
  typeFilter,
  categoryFilter,
  onTypeFilterChange,
  onCategoryFilterChange,
  onEdit,
  onDeleted,
}: FinancesTransactionListProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const categoryOptions =
    typeFilter === "all"
      ? [...categoriesForType("expense"), ...categoriesForType("income")]
      : categoriesForType(typeFilter);

  useEffect(() => {
    if (categoryFilter !== "all" && !categoryOptions.includes(categoryFilter)) {
      onCategoryFilterChange("all");
    }
  }, [categoryFilter, categoryOptions, onCategoryFilterChange]);

  async function handleDelete(id: string) {
    if (!window.confirm("Supprimer cette transaction ?")) return;
    setDeletingId(id);
    try {
      await deleteFinanceTransaction(id);
      toast.success("Transaction supprimée");
      onDeleted();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    } finally {
      setDeletingId(null);
    }
  }

  function formatDate(dateStr: string): string {
    try {
      return format(parseISO(dateStr.slice(0, 10)), "d MMM yyyy", { locale: fr });
    } catch {
      return dateStr;
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <Select
          value={typeFilter}
          onValueChange={(v) => onTypeFilterChange(v as "all" | TransactionType)}
        >
          <SelectTrigger className="w-[160px] border-white/10 bg-surface/60">
            <SelectValue placeholder="Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tout</SelectItem>
            <SelectItem value="income">Revenus</SelectItem>
            <SelectItem value="expense">Dépenses</SelectItem>
          </SelectContent>
        </Select>

        <Select value={categoryFilter} onValueChange={onCategoryFilterChange}>
          <SelectTrigger className="w-[180px] border-white/10 bg-surface/60">
            <SelectValue placeholder="Catégorie" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Toutes catégories</SelectItem>
            {categoryOptions.map((cat) => (
              <SelectItem key={cat} value={cat}>
                {CATEGORY_LABELS[cat] ?? cat}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {transactions.length === 0 ? (
        <p className="rounded-xl border border-dashed border-white/10 px-4 py-8 text-center text-sm text-titanium">
          Aucune transaction pour ce mois.
        </p>
      ) : (
        <ul className="divide-y divide-white/5 rounded-xl border border-white/10 bg-surface/40">
          {transactions.map((tx) => {
            const Icon = CATEGORY_ICONS[tx.category] ?? Wallet;
            const isIncome = tx.type === "income";
            return (
              <li
                key={tx.id}
                className="flex items-center gap-3 px-4 py-3 transition hover:bg-white/[0.02]"
              >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white/5">
                  <Icon className="h-4 w-4 text-copper-glow" />
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="truncate text-sm font-medium text-ivory">
                      {tx.description?.trim() ||
                        CATEGORY_LABELS[tx.category] ||
                        tx.category}
                    </p>
                    {tx.project_name ? (
                      <Badge variant="outline" className="border-white/10 text-xs">
                        {tx.project_name}
                      </Badge>
                    ) : null}
                    {tx.is_recurring ? (
                      <Badge
                        variant="outline"
                        className="gap-1 border-copper/30 text-xs text-copper-glow"
                      >
                        <Repeat className="h-3 w-3" />
                        Récurrent
                      </Badge>
                    ) : null}
                  </div>
                  <p className="text-xs text-titanium">{formatDate(tx.date)}</p>
                </div>

                <p
                  className={cn(
                    "shrink-0 text-sm font-semibold tabular-nums",
                    isIncome ? "text-emerald-400" : "text-red-400"
                  )}
                >
                  {isIncome ? "+" : "−"}
                  {formatCurrency(tx.amount, tx.currency)}
                </p>

                <div className="flex shrink-0 gap-1">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-titanium hover:text-ivory"
                    onClick={() => onEdit(tx)}
                    aria-label="Modifier"
                  >
                    <Pencil className="h-3.5 w-3.5" />
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-titanium hover:text-red-400"
                    disabled={deletingId === tx.id}
                    onClick={() => handleDelete(tx.id)}
                    aria-label="Supprimer"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
