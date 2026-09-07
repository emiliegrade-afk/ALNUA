"use client";

import { ConsoleProvider } from "@/components/console/console-provider";
import { DeptV2PageShell } from "@/components/dept-v2";
import { AgentTrustView } from "@/components/trust/agent-trust-view";
import { CrossDeptQueuePanel } from "@/components/trust/cross-dept-queue-panel";
import { ReviewBoardPanel } from "@/components/trust/review-board-panel";
import { C } from "@/app/app-v2/shared";
import { ROUTES } from "@/lib/routes";

/** Phase 31 — trust + Review Board + cross-dept drain (Phase 36). */
export default function TrustPage() {
  return (
    <ConsoleProvider>
      <DeptV2PageShell deptHref={ROUTES.hub} activeDeptId="hub" coreSubtitle="Trust agents">
        <div
          className="alnua-scroll flex min-w-0 flex-1 flex-col gap-4 overflow-y-auto px-4 pb-4 pt-3.5"
          style={{ color: C.ivory }}
        >
          <div>
            <h1 className="text-[23px] leading-[1.1] tracking-[1px]">
              <span className="font-bold">AGENT</span>{" "}
              <span className="font-light tracking-[4px]" style={{ color: C.titanium }}>
                TRUST
              </span>
            </h1>
            <p className="mt-0.5 text-[11px]" style={{ color: C.dim }}>
              Fiabilité · Review Board · orchestration inter-départements
            </p>
          </div>
          <CrossDeptQueuePanel />
          <ReviewBoardPanel />
          <AgentTrustView />
        </div>
      </DeptV2PageShell>
    </ConsoleProvider>
  );
}
