"use client";

import { AnalyticsAgentsPanel } from "@/components/analytics/analytics-agents-panel";
import { ConsoleProvider } from "@/components/console/console-provider";
import { DeptV2PageShell } from "@/components/dept-v2";
import { C } from "@/app/app-v2/shared";
import { ROUTES } from "@/lib/routes";
import Link from "next/link";

/**
 * Analytics department — Layla / Axel tools + links to real measurement surfaces.
 */
export default function AnalyticsPage() {
  return (
    <ConsoleProvider>
      <DeptV2PageShell
        deptHref={ROUTES.analytics}
        activeDeptId="analytics"
        coreSubtitle="Mesure"
      >
        <div
          className="alnua-scroll flex min-w-0 flex-1 flex-col gap-6 overflow-y-auto px-4 pb-4 pt-3.5"
          style={{ color: C.ivory }}
        >
          <div>
            <h1 className="text-[23px] leading-[1.1] tracking-[1px]">
              <span className="font-bold">ANALYTICS</span>{" "}
              <span className="font-light tracking-[4px]" style={{ color: C.titanium }}>
                MESURE
              </span>
            </h1>
            <p className="mt-0.5 text-[11px]" style={{ color: C.dim }}>
              Layla (business) · Axel (data) — sources réelles, pas de KPI inventés
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <Link
              href={ROUTES.marketing}
              className="rounded-[10px] border px-4 py-3 transition-colors hover:bg-obsidian-2/80"
              style={{ borderColor: C.line }}
            >
              <span className="block text-[13px] font-medium" style={{ color: C.copperLight }}>
                Marketing — performances
              </span>
              <span className="mt-1 block text-[11px]" style={{ color: C.dim }}>
                Reach / engagement saisis manuellement (Phase 37)
              </span>
            </Link>
            <Link
              href={ROUTES.finances}
              className="rounded-[10px] border px-4 py-3 transition-colors hover:bg-obsidian-2/80"
              style={{ borderColor: C.line }}
            >
              <span className="block text-[13px] font-medium" style={{ color: C.copperLight }}>
                Finance — coûts LLM
              </span>
              <span className="mt-1 block text-[11px]" style={{ color: C.dim }}>
                Coûts & factures SaaS réels
              </span>
            </Link>
          </div>

          <AnalyticsAgentsPanel />
        </div>
      </DeptV2PageShell>
    </ConsoleProvider>
  );
}
