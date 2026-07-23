import { FinancesView } from "@/components/finances/finances-view";
import { BureauAgentsSection } from "@/components/shared/bureau-agents-section";
import { BureauPage } from "@/components/shared/bureau-page";

export default function FinancesPage() {
  return (
    <BureauPage
      dept="finances"
      title="Comptabilité"
      subtitle="Jules · Rémi · Finances · Coûts LLM · Budget"
      breadcrumb="Comptabilité"
    >
      <BureauAgentsSection bureau="finances" />
      <FinancesView />
    </BureauPage>
  );
}
