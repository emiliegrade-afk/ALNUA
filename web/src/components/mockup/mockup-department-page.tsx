"use client";

import type { ReactNode } from "react";
import { useConsoleData } from "@/components/console/console-provider";
import { getConsoleDepartment } from "@/lib/console/departments";
import { ProtoFullShell } from "./prototype/proto-full-shell";
import { MockupDashboardView } from "./views/dashboard-view";
import { MockupCeoView } from "./views/ceo-view";
import { MockupHubView } from "./views/hub-view";
import { MockupSecretaryView } from "./views/secretary-view";
import { MockupRdView } from "./views/rd-view";
import { MockupAppView } from "./views/app-view";
import { MockupGamingView } from "./views/gaming-view";
import { MockupRoboView } from "./views/robo-view";
import { MockupMarketingView } from "./views/marketing-view";
import { MockupFinancesView } from "./views/finances-view";
import { MockupAnalyticsView } from "./views/analytics-view";
import { MockupBrandView } from "./views/brand-view";

export interface MockupDepartmentPageProps {
  deptId: string;
}

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
    case "rd":
      view = <MockupRdView department={department} />;
      break;
    case "app":
      view = <MockupAppView department={department} />;
      break;
    case "gaming":
      view = <MockupGamingView department={department} />;
      break;
    case "robo":
      view = <MockupRoboView department={department} />;
      break;
    case "marketing":
      view = <MockupMarketingView department={department} />;
      break;
    case "finances":
      view = <MockupFinancesView department={department} />;
      break;
    case "analytics":
      view = <MockupAnalyticsView department={department} />;
      break;
    case "brand":
      view = <MockupBrandView department={department} />;
      break;
    default:
      view = <MockupDashboardView />;
  }

  return <ProtoFullShell>{view}</ProtoFullShell>;
}
