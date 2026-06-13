import { AnalyticsView } from "@/components/analytics/analytics-view";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { BureauAgentsSection } from "@/components/shared/bureau-agents-section";
import { DepartmentHeader } from "@/components/shared/department-header";

export default function AnalyticsPage() {
  return (
    <>
      <BackToLobby />
      <DepartmentHeader
        dept="analytics"
        title="Reporting & Analytics"
        subtitle="Layla · Axel · KPIs · Métriques · Releases"
      />
      <BureauAgentsSection bureau="analytics" />
      <AnalyticsView />
    </>
  );
}
