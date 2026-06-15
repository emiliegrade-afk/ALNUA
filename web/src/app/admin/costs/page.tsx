import { AdminCostsView } from "@/components/admin/costs/admin-costs-view";
import { AdminGate } from "@/components/admin/admin-gate";
import { AdminShell } from "@/components/admin/admin-shell";

export default function AdminCostsPage() {
  return (
    <AdminGate page="costs" title="Coûts LLM">
      <AdminShell
        title="Coûts LLM"
        subtitle="Rémi · Jules · cost_monitor — rapport, budget, top appels"
      >
        <AdminCostsView />
      </AdminShell>
    </AdminGate>
  );
}
