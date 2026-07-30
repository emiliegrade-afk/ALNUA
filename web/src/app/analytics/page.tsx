import { AnalyticsAgentsPanel } from "@/components/analytics/analytics-agents-panel";
import { AnalyticsView } from "@/components/analytics/analytics-view";
import { BureauPage } from "@/components/shared/bureau-page";
import { DepartmentWorkspace } from "@/components/shared/department-workspace";

export default function AnalyticsPage() {
  return (
    <BureauPage
      dept="analytics"
      bureau="analytics"
      title="Reporting & Analytics"
      subtitle="Layla · Axel · KPIs · Métriques · Releases"
    >
      <DepartmentWorkspace bureau="analytics" dept="analytics" projectBranch={null} />
      <AnalyticsAgentsPanel />
      <AnalyticsView />
    </BureauPage>
  );
}
