import { FinancesView } from "@/components/finances/finances-view";
import { BureauPage } from "@/components/shared/bureau-page";
import { DepartmentWorkspace } from "@/components/shared/department-workspace";

export default function FinancesPage() {
  return (
    <BureauPage
      dept="finances"
      bureau="finances"
      title="Comptabilité"
      subtitle="Jules · Rémi · Finances · Coûts LLM · Budget"
      breadcrumb="Comptabilité"
    >
      <DepartmentWorkspace bureau="finances" dept="finances" projectBranch={null} />
      <FinancesView />
    </BureauPage>
  );
}
