"use client";

import { ConsoleProvider } from "@/components/console/console-provider";
import { DeptV2PageShell } from "@/components/dept-v2";
import { C } from "@/app/app-v2/shared";
import { ROUTES } from "@/lib/routes";
import Link from "next/link";

/**
 * Live Direction / Hub shell — ops links + real cockpit entry points.
 * Replaces the former mockup department shell for /hub.
 */
export default function HubPage() {
  return (
    <ConsoleProvider>
      <DeptV2PageShell deptHref={ROUTES.hub} activeDeptId="hub" coreSubtitle="Direction ops">
        <div
          className="alnua-scroll flex min-w-0 flex-1 flex-col gap-4 overflow-y-auto px-4 pb-4 pt-3.5"
          style={{ color: C.ivory }}
        >
          <div>
            <h1 className="text-[23px] leading-[1.1] tracking-[1px]">
              <span className="font-bold">DIRECTION</span>{" "}
              <span className="font-light tracking-[4px]" style={{ color: C.titanium }}>
                HUB
              </span>
            </h1>
            <p className="mt-0.5 text-[11px]" style={{ color: C.dim }}>
              Ops · workflows · CEO · coûts
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {[
              { href: ROUTES.ceo, label: "CEO Cockpit", desc: "Gate Academy · dossiers" },
              { href: ROUTES.activity, label: "Activité", desc: "Feed live agents" },
              { href: ROUTES.finances, label: "Finance", desc: "Trésorerie · factures" },
              { href: "/admin", label: "Admin", desc: "Flags · coûts LLM" },
              { href: ROUTES.trust, label: "Agent Trust", desc: "Fiabilité ≠ compétition" },
              { href: ROUTES.academy, label: "Académie", desc: "Pipeline agents" },
              { href: ROUTES.settings, label: "Réglages", desc: "Modèles · clés" },
            ].map((card) => (
              <Link
                key={card.href}
                href={card.href}
                className="rounded-[10px] border px-4 py-3 transition-colors hover:bg-obsidian-2/80"
                style={{ borderColor: C.line, color: C.ivory }}
              >
                <span className="block text-[13px] font-medium" style={{ color: C.copperLight }}>
                  {card.label}
                </span>
                <span className="mt-1 block text-[11px]" style={{ color: C.dim }}>
                  {card.desc}
                </span>
              </Link>
            ))}
          </div>
        </div>
      </DeptV2PageShell>
    </ConsoleProvider>
  );
}
