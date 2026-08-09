"use client";

import { useMemo, useState } from "react";
import { ChevronDown, ChevronUp, Repeat, Settings2 } from "lucide-react";
import {
  CATEGORY_LABELS,
  RECURRENCE_LABELS,
} from "@/components/finances/finances.constants";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency, type FinanceTransaction, type Recurrence } from "@/lib/finances-api";

interface FinancesRecurringSectionProps {
  items: FinanceTransaction[];
  onManage: (tx: FinanceTransaction) => void;
}

export function FinancesRecurringSection({
  items,
  onManage,
}: FinancesRecurringSectionProps) {
  const [open, setOpen] = useState(false);

  const grouped = useMemo(() => {
    const map: Record<string, FinanceTransaction[]> = {};
    for (const tx of items) {
      const key = tx.recurrence ?? "monthly";
      map[key] = map[key] ?? [];
      map[key].push(tx);
    }
    return map;
  }, [items]);

  if (items.length === 0) return null;

  const order: Recurrence[] = ["monthly", "annual", "one_time"];

  return (
    <Card className="border-copper/15 bg-surface/80">
      <CardHeader className="pb-2">
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          className="flex w-full items-center justify-between text-left"
        >
          <CardTitle className="flex items-center gap-2 text-sm font-medium text-ivory">
            <Repeat className="h-4 w-4 text-copper" />
            Abonnements &amp; dépenses récurrentes
            <Badge variant="outline" className="ml-1 border-copper/30 text-copper-glow">
              {items.length}
            </Badge>
          </CardTitle>
          {open ? (
            <ChevronUp className="h-4 w-4 text-titanium" />
          ) : (
            <ChevronDown className="h-4 w-4 text-titanium" />
          )}
        </button>
      </CardHeader>

      {open ? (
        <CardContent className="space-y-4 pt-0">
          {order.map((freq) => {
            const group = grouped[freq];
            if (!group?.length) return null;
            return (
              <div key={freq}>
                <p className="mb-2 text-xs font-medium uppercase tracking-wide text-titanium">
                  {RECURRENCE_LABELS[freq]}
                </p>
                <ul className="space-y-2">
                  {group.map((tx) => (
                    <li
                      key={tx.id}
                      className="flex items-center justify-between rounded-lg border border-copper/10 bg-obsidian-deep/40 px-3 py-2"
                    >
                      <div>
                        <p className="text-sm text-ivory">
                          {tx.description?.trim() ||
                            CATEGORY_LABELS[tx.category] ||
                            tx.category}
                        </p>
                        {tx.project_name ? (
                          <p className="text-xs text-titanium">{tx.project_name}</p>
                        ) : null}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium tabular-nums text-red-400">
                          {formatCurrency(tx.amount, tx.currency)}
                        </span>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="h-8 text-titanium hover:text-ivory"
                          onClick={() => onManage(tx)}
                        >
                          <Settings2 className="mr-1 h-3.5 w-3.5" />
                          Gérer
                        </Button>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </CardContent>
      ) : null}
    </Card>
  );
}
