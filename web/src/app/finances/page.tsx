import { FinancesView } from "@/components/finances/finances-view";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { DepartmentHeader } from "@/components/shared/department-header";

export default function FinancesPage() {
  return (
    <>
      <BackToLobby />
      <DepartmentHeader
        dept="finances"
        title="Comptabilité"
        subtitle="Finances · Coûts LLM · Budget · Transactions"
        breadcrumb="Comptabilité"
      />
      <FinancesView />
    </>
  );
}
