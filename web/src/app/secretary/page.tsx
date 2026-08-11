"use client";

import { ConsoleProvider } from "@/components/console/console-provider";
import { DeptV2PageShell } from "@/components/dept-v2";
import { AssistantChat } from "@/components/assistant/assistant-chat";
import { NadiaDesktopPanel } from "@/components/secretary/nadia-desktop-panel";
import { NadiaToolsPanel } from "@/components/secretary/nadia-tools-panel";
import { SavLitePanel } from "@/components/secretary/sav-lite-panel";
import { SecretaryConsole } from "@/components/secretary/secretary-console";
import { BureauIdentityStrip } from "@/components/shared/bureau-identity-strip";
import { C } from "@/app/app-v2/shared";
import { ROUTES } from "@/lib/routes";
import Link from "next/link";

/** Live Secrétariat — Nadia filtre le quotidien CEO. */
export default function SecretaryPage() {
  return (
    <ConsoleProvider>
      <DeptV2PageShell
        deptHref={ROUTES.secretary}
        activeDeptId="secretary"
        coreSubtitle="Bureau Nadia"
      >
        <div
          className="alnua-scroll flex min-w-0 flex-1 flex-col gap-4 overflow-y-auto px-4 pb-4 pt-3.5"
          style={{ color: C.ivory }}
        >
          <div>
            <h1 className="text-[23px] leading-[1.1] tracking-[1px]">
              <span className="font-bold">SECRÉTARIAT</span>{" "}
              <span className="font-light tracking-[4px]" style={{ color: C.titanium }}>
                NADIA
              </span>
            </h1>
            <p className="mt-0.5 text-[11px]" style={{ color: C.dim }}>
              Filtre CEO · docs · ménage PC · SAV · Academy · escalade{" "}
              <Link href={ROUTES.legal} className="text-copper hover:underline">
                juridique
              </Link>
            </p>
          </div>
          <BureauIdentityStrip
            agentId="secretary"
            name="Nadia Faure"
            role="Secrétaire de direction — mails, agenda, docs"
            href={ROUTES.hq}
            hrefLabel="Plan HQ"
          />
          <NadiaDesktopPanel />
          <div className="min-h-[400px]">
            <AssistantChat variant="secretary" defaultAgent="secretary" />
          </div>
          <NadiaToolsPanel />
          <SavLitePanel />
          <SecretaryConsole />
        </div>
      </DeptV2PageShell>
    </ConsoleProvider>
  );
}
