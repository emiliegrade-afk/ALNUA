import { FinancesView } from "@/components/finances/finances-view";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { BureauAgentsSection } from "@/components/shared/bureau-agents-section";
import { DepartmentHeader } from "@/components/shared/department-header";

export default function FinancesPage() {
  return (
    <>
      <BackToLobby />
      <DepartmentHeader
        dept="finances"
        title="Comptabilité"
        subtitle="Jules · Rémi · Finances · Coûts LLM · Budget"
        breadcrumb="Comptabilité"
      />
      <BureauAgentsSection bureau="finances" />
      <FinancesView />
    </>
  );
}
