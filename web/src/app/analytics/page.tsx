import { AnalyticsAgentsPanel } from "@/components/analytics/analytics-agents-panel";
import { AnalyticsView } from "@/components/analytics/analytics-view";
import { BureauAgentsSection } from "@/components/shared/bureau-agents-section";
import { BureauPage } from "@/components/shared/bureau-page";

export default function AnalyticsPage() {
  return (
    <BureauPage
      dept="analytics"
      title="Reporting & Analytics"
      subtitle="Layla · Axel · KPIs · Métriques · Releases"
    >
      <BureauAgentsSection bureau="analytics" />
      <AnalyticsAgentsPanel />
      <AnalyticsView />
    </BureauPage>
  );
}
