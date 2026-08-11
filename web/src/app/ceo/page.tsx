"use client";

import { ConsoleProvider } from "@/components/console/console-provider";
import { DeptV2PageShell } from "@/components/dept-v2";
import { CeoIdleQueueCard } from "@/components/ceo/ceo-idle-queue-card";
import { CeoMorningBriefCard } from "@/components/ceo/ceo-morning-brief-card";
import { CeoPendingDossiersCard } from "@/components/ceo/ceo-pending-dossiers-card";
import { CeoUserManualCard } from "@/components/ceo/ceo-user-manual-card";
import { CeoWorkflowsPendingCard } from "@/components/ceo/ceo-workflows-pending-card";
import { CeoCockpitPanel } from "@/components/hub/ceo-cockpit";
import { AssistantChat } from "@/components/assistant/assistant-chat";
import { C } from "@/app/app-v2/shared";
import { ROUTES } from "@/lib/routes";

/** Live CEO cockpit — replaces the former mockup department shell. */
export default function CeoPage() {
  return (
    <ConsoleProvider>
      <DeptV2PageShell deptHref={ROUTES.ceo} activeDeptId="hub" coreSubtitle="Décisions CEO">
        <div
          className="alnua-scroll flex min-w-0 flex-1 flex-col gap-4 overflow-y-auto px-4 pb-4 pt-3.5"
          style={{ color: C.ivory }}
        >
          <div>
            <h1 className="text-[23px] leading-[1.1] tracking-[1px]">
              <span className="font-bold">CEO</span>{" "}
              <span className="font-light tracking-[4px]" style={{ color: C.titanium }}>
                COCKPIT
              </span>
            </h1>
            <p className="mt-0.5 text-[11px]" style={{ color: C.dim }}>
              Brief · décisions · dossiers · autonomie
            </p>
          </div>
          <CeoMorningBriefCard />
          <CeoUserManualCard />
          <CeoPendingDossiersCard />
          <CeoIdleQueueCard />
          <CeoWorkflowsPendingCard />
          <CeoCockpitPanel />
          <div className="min-h-[420px]">
            <AssistantChat variant="ceo" defaultAgent="auto" />
          </div>
        </div>
      </DeptV2PageShell>
    </ConsoleProvider>
  );
}
