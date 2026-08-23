"use client";

import { ConsoleProvider } from "@/components/console/console-provider";
import { DeptV2PageShell } from "@/components/dept-v2";
import { CeoPendingDossiersCard } from "@/components/ceo/ceo-pending-dossiers-card";
import { CeoIdleQueueCard } from "@/components/ceo/ceo-idle-queue-card";
import { CeoWorkflowsPendingCard } from "@/components/ceo/ceo-workflows-pending-card";
import { AssistantChat } from "@/components/assistant/assistant-chat";
import { CeoCommandView } from "@/components/siege/ceo-command-view";
import { C } from "@/app/app-v2/shared";
import { ROUTES } from "@/lib/routes";
import Link from "next/link";

/** Bureau CEO — maquette command center + actions live (dossiers / chat). */
export default function CeoPage() {
  return (
    <ConsoleProvider>
      <DeptV2PageShell deptHref={ROUTES.ceo} activeDeptId="ceo" coreSubtitle="Bureau du CEO">
        <div
          className="alnua-scroll flex min-w-0 flex-1 flex-col gap-5 overflow-y-auto px-4 pb-4 pt-3.5"
          style={{ color: C.ivory }}
        >
          <CeoCommandView />

          <div className="grid gap-4 lg:grid-cols-2">
            <CeoPendingDossiersCard />
            <CeoWorkflowsPendingCard />
          </div>
          <div className="min-w-0">
            <CeoIdleQueueCard />
          </div>

          <div className="min-h-[340px] rounded-xl border border-copper/20 bg-obsidian/40 p-1">
            <AssistantChat variant="ceo" defaultAgent="auto" embedded />
          </div>

          <p className="text-[11px]" style={{ color: C.dim }}>
            Docs & contrats →{" "}
            <Link href={ROUTES.secretary} className="text-copper hover:underline">
              Secrétariat Nadia
            </Link>
            {" · "}
            <Link href={ROUTES.legal} className="text-copper hover:underline">
              Solène
            </Link>
          </p>
        </div>
      </DeptV2PageShell>
    </ConsoleProvider>
  );
}
