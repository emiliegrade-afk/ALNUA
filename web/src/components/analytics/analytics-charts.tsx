"use client";

import dynamic from "next/dynamic";
import { Loader2 } from "lucide-react";
import { RecentFeedbackTable } from "@/components/analytics/recent-feedback-table";
import type { AnalyticsRow, FeedbackRow, RevenueMonth } from "@/lib/analytics";
import type { Project } from "@/lib/types";
import type { TicketWithProject } from "@/lib/tickets";

function ChartLoader() {
  return (
    <div className="flex min-h-[280px] items-center justify-center">
      <Loader2 className="h-6 w-6 animate-spin text-copper/50" />
    </div>
  );
}

const DownloadsChart = dynamic(
  () =>
    import("@/components/analytics/downloads-chart").then((m) => m.DownloadsChart),
  { ssr: false, loading: ChartLoader }
);

const RevenueChart = dynamic(
  () =>
    import("@/components/analytics/revenue-chart").then((m) => m.RevenueChart),
  { ssr: false, loading: ChartLoader }
);

const RatingsChart = dynamic(
  () =>
    import("@/components/analytics/ratings-chart").then((m) => m.RatingsChart),
  { ssr: false, loading: ChartLoader }
);

const ProjectAccordion = dynamic(
  () =>
    import("@/components/analytics/project-accordion").then(
      (m) => m.ProjectAccordion
    ),
  { ssr: false, loading: ChartLoader }
);

export function AnalyticsChartsSection({
  analyticsRows,
  projects,
  projectFilter,
  revenueMonths,
  feedback,
  tickets,
  onAddMetric,
}: {
  analyticsRows: AnalyticsRow[];
  projects: Project[];
  projectFilter: string;
  revenueMonths: RevenueMonth[];
  feedback: FeedbackRow[];
  tickets: TicketWithProject[];
  onAddMetric: () => void;
}) {
  return (
    <>
      <div className="grid gap-4 xl:grid-cols-2">
        <DownloadsChart
          rows={analyticsRows}
          projects={projects}
          projectFilter={projectFilter}
          onAddMetric={onAddMetric}
        />
        <RevenueChart months={revenueMonths} onAddMetric={onAddMetric} />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <RatingsChart
          feedback={feedback}
          projects={
            projectFilter === "all"
              ? projects
              : projects.filter((p) => p.id === projectFilter)
          }
          projectFilter={projectFilter}
        />
        <RecentFeedbackTable feedback={feedback} projects={projects} />
      </div>

      <ProjectAccordion
        projects={projects}
        analyticsRows={analyticsRows}
        tickets={tickets}
      />
    </>
  );
}

export { DownloadsChart, RevenueChart, RatingsChart, ProjectAccordion };
