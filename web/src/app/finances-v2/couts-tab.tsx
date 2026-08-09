"use client";

import { ApiCostsCard } from "@/components/finances/api-costs-card";
import { SaasInvoicesPanel } from "@/components/finances/saas-invoices-panel";

/* Onglet Coûts — API live + abonnements SaaS + factures + Revolut status. */

export function CoutsTab() {
  return (
    <div className="alnua-scroll flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-1">
      <ApiCostsCard />
      <SaasInvoicesPanel />
    </div>
  );
}
