"use client";

import type { ReactNode } from "react";
import { useConsoleData } from "@/components/console/console-provider";
import { getConsoleDepartment } from "@/lib/console/departments";
import { ProtoFullShell } from "./prototype/proto-full-shell";
import { MockupDashboardView } from "./views/dashboard-view";
import { MockupCeoView } from "./views/ceo-view";
import { MockupHubView } from "./views/hub-view";
import { MockupSecretaryView } from "./views/secretary-view";
import { MockupAnalyticsView } from "./views/analytics-view";

export interface MockupDepartmentPageProps {
  deptId: string;
}

/**
 * Mockup shell for departments without a live *-v2 Command Center yet
 * (hub / ceo / secretary / analytics). Brand → BrandView; finances/marketing/app…
 * → thin re-exports of *-v2.
 */
export function MockupDepartmentPage({ deptId }: MockupDepartmentPageProps) {
  const { stats, liveAgents } = useConsoleData();
  const department = getConsoleDepartment(deptId, liveAgents, stats);

  if (!department) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm text-titane/60">Département inconnu.</p>
      </div>
    );
  }

  let view: ReactNode;
  switch (deptId) {
    case "ceo":
      view = <MockupCeoView department={department} />;
      break;
    case "hub":
      view = <MockupHubView department={department} />;
      break;
    case "secretary":
      view = <MockupSecretaryView department={department} />;
      break;
    case "analytics":
      view = <MockupAnalyticsView department={department} />;
      break;
    default:
      view = <MockupDashboardView />;
  }

  return <ProtoFullShell>{view}</ProtoFullShell>;
}
