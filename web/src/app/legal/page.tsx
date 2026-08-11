"use client";

import { ConsoleProvider } from "@/components/console/console-provider";
import { DeptV2PageShell } from "@/components/dept-v2";
import { LegalCounselPanel } from "@/components/secretary/legal-counsel-panel";
import { LegalPersonaCard } from "@/components/legal/legal-persona-card";
import { C } from "@/app/app-v2/shared";
import { ROUTES } from "@/lib/routes";
import Link from "next/link";

/** Bureau juridique — Solène Hariri (indépendante de Nadia). */
export default function LegalPage() {
  return (
    <ConsoleProvider>
      <DeptV2PageShell
        deptHref={ROUTES.legal}
        activeDeptId="legal"
        coreSubtitle="Conseil juridique"
      >
        <div
          className="alnua-scroll flex min-w-0 flex-1 flex-col gap-4 overflow-y-auto px-4 pb-4 pt-3.5"
          style={{ color: C.ivory }}
        >
          <div>
            <h1 className="text-[23px] leading-[1.1] tracking-[1px]">
              <span className="font-bold">BUREAU</span>{" "}
              <span className="font-light tracking-[4px]" style={{ color: C.titanium }}>
                JURIDIQUE
              </span>
            </h1>
            <p className="mt-0.5 text-[11px]" style={{ color: C.dim }}>
              Solène Hariri · droit des affaires UE / USA / Asie · relecture avant signature
            </p>
            <p className="mt-2 text-[11px]" style={{ color: C.dim }}>
              Escalade depuis{" "}
              <Link href={ROUTES.secretary} className="text-copper hover:underline">
                Nadia
              </Link>{" "}
              · templates contrats enrichis
            </p>
          </div>
          <LegalPersonaCard />
          <LegalCounselPanel />
        </div>
      </DeptV2PageShell>
    </ConsoleProvider>
  );
}
