"use client";

import { ConsoleProvider } from "@/components/console/console-provider";
import { DeptV2PageShell } from "@/components/dept-v2";
import { AssistantChat } from "@/components/assistant/assistant-chat";
import { NadiaDesktopPanel } from "@/components/secretary/nadia-desktop-panel";
import { NadiaToolsPanel } from "@/components/secretary/nadia-tools-panel";
import { SavLitePanel } from "@/components/secretary/sav-lite-panel";
import { BureauIdentityStrip } from "@/components/shared/bureau-identity-strip";
import { BureauRoster } from "@/components/shared/bureau-roster";
import { SiegeLifeLinks } from "@/components/shared/siege-life-links";
import { C } from "@/app/app-v2/shared";
import { ROUTES } from "@/lib/routes";
import Link from "next/link";

/** Secrétariat — chat + outils Hub (docs/contrats Word), pas d'éditeur desktop. */
export default function SecretaryPage() {
  return (
    <ConsoleProvider>
      <DeptV2PageShell
        deptHref={ROUTES.secretary}
        activeDeptId="secretary"
        coreSubtitle="Bureau Nadia"
      >
        <div
          className="alnua-scroll flex min-w-0 flex-1 flex-col gap-5 overflow-y-auto px-4 pb-4 pt-3.5"
          style={{ color: C.ivory }}
        >
          <header className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h1 className="text-[26px] leading-[1.05] tracking-[1px]">
                <span className="font-bold">SECRÉTARIAT</span>{" "}
                <span className="font-light tracking-[0.35em]" style={{ color: C.titanium }}>
                  NADIA
                </span>
              </h1>
              <p className="mt-1 text-[12px]" style={{ color: C.dim }}>
                Mails · agenda · docs Word · contrats · ménage PC · escalade{" "}
                <Link href={ROUTES.legal} className="text-copper hover:underline">
                  Solène
                </Link>
              </p>
            </div>
            <SiegeLifeLinks />
          </header>

          <BureauIdentityStrip
            agentId="secretary"
            name="Nadia Faure"
            role="Secrétaire — traitement de texte & organisation dans le Hub"
            href={ROUTES.legal}
            hrefLabel="Avocate"
          />

          <NadiaDesktopPanel />

          <div className="min-h-[400px] border border-titanium/20 bg-transparent p-1">
            <AssistantChat variant="secretary" defaultAgent="secretary" embedded />
          </div>

          <NadiaToolsPanel />
          <BureauRoster bureau="secretary" title="Bureau Nadia · Clara" />
          <SavLitePanel />
        </div>
      </DeptV2PageShell>
    </ConsoleProvider>
  );
}
