import { AnalyticsView } from "@/components/analytics/analytics-view";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { DepartmentHeader } from "@/components/shared/department-header";

export default function AnalyticsPage() {
  return (
    <>
      <BackToLobby />
      <DepartmentHeader
        dept="analytics"
        title="Reporting"
        subtitle="Analytics · KPIs · Métriques · Releases"
      />
      <AnalyticsView />
    </>
  );
}
