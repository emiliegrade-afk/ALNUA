"use client";

import { ConsoleProvider } from "@/components/console/console-provider";
import { DeptV2PageShell } from "@/components/dept-v2";
import { CeoMorningBriefCard } from "@/components/ceo/ceo-morning-brief-card";
import { CeoPendingDossiersCard } from "@/components/ceo/ceo-pending-dossiers-card";
import { CeoIdleQueueCard } from "@/components/ceo/ceo-idle-queue-card";
import { CeoWorkflowsPendingCard } from "@/components/ceo/ceo-workflows-pending-card";
import { AssistantChat } from "@/components/assistant/assistant-chat";
import { BureauIdentityStrip } from "@/components/shared/bureau-identity-strip";
import { BureauRoster } from "@/components/shared/bureau-roster";
import { SiegeLifeLinks } from "@/components/shared/siege-life-links";
import { C } from "@/app/app-v2/shared";
import { ROUTES } from "@/lib/routes";
import Link from "next/link";

/** Bureau CEO — void + cuivre, pas de slabs gris. */
export default function CeoPage() {
  return (
    <ConsoleProvider>
      <DeptV2PageShell deptHref={ROUTES.ceo} activeDeptId="hub" coreSubtitle="Décisions CEO">
        <div
          className="alnua-scroll flex min-w-0 flex-1 flex-col gap-5 overflow-y-auto px-4 pb-4 pt-3.5"
          style={{ color: C.ivory }}
        >
          <header className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h1 className="text-[26px] leading-[1.05] tracking-[1px]">
                <span className="font-bold">CEO</span>{" "}
                <span className="font-light tracking-[0.35em]" style={{ color: C.titanium }}>
                  EMILIE
                </span>
              </h1>
              <p className="mt-1 text-[12px]" style={{ color: C.dim }}>
                Brief du jour · décisions · équipe Direction
              </p>
            </div>
            <SiegeLifeLinks />
          </header>

          <BureauIdentityStrip
            agentId="coo"
            name="Aria Voss"
            role="COO — filtre stratégique & délégation"
            href={ROUTES.hub}
            hrefLabel="Direction"
          />

          <CeoMorningBriefCard />

          <div className="grid gap-4 lg:grid-cols-2">
            <CeoPendingDossiersCard />
            <CeoWorkflowsPendingCard />
          </div>
          <CeoIdleQueueCard />

          <BureauRoster bureau="hub" title="Direction — portraits" />

          <div className="min-h-[380px] border border-titanium/20 bg-transparent p-1">
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
