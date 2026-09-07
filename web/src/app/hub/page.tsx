"use client";

import { ConsoleProvider } from "@/components/console/console-provider";
import { DeptV2PageShell } from "@/components/dept-v2";
import { DirectionCommandView } from "@/components/siege/direction-command-view";
import { HubWorkflowsPanel } from "@/components/hub/hub-workflows-panel";
import { BureauRoster } from "@/components/shared/bureau-roster";
import { SiegeLifeLinks } from "@/components/shared/siege-life-links";
import { C } from "@/app/app-v2/shared";
import { ROUTES } from "@/lib/routes";
import Link from "next/link";

const OPS = [
  { href: ROUTES.ceo, label: "CEO", desc: "Brief · workflows · idle" },
  { href: ROUTES.secretary, label: "Secrétariat", desc: "Nadia · docs · mails" },
  { href: ROUTES.legal, label: "Juridique", desc: "Solène · contrats" },
  { href: ROUTES.activity, label: "Activité", desc: "Feed live" },
  { href: ROUTES.academy, label: "Académie", desc: "Pipeline agents" },
  { href: ROUTES.trust, label: "Trust", desc: "Fiabilité · cross-dept" },
  { href: ROUTES.finances, label: "Finance", desc: "Budget · factures" },
  { href: ROUTES.settings, label: "Réglages", desc: "Modèles · clés" },
] as const;

/** Direction — management + workflows Company OS (Phase 30). */
export default function HubPage() {
  return (
    <ConsoleProvider>
      <DeptV2PageShell deptHref={ROUTES.hub} activeDeptId="hub" coreSubtitle="Direction ops">
        <div
          className="alnua-scroll flex min-w-0 flex-1 flex-col gap-5 overflow-y-auto px-4 pb-4 pt-3.5"
          style={{ color: C.ivory }}
        >
          <DirectionCommandView />
          <HubWorkflowsPanel />
          <SiegeLifeLinks />
          <BureauRoster bureau="hub" title="Équipe Direction — détail" />
          <section className="rounded-xl border border-copper/20 bg-obsidian/55 p-3">
            <p className="mb-3 text-[10px] uppercase tracking-[0.2em] text-titanium/55">
              Accès ops
            </p>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
              {OPS.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="rounded-lg border border-copper/25 px-3 py-2.5 transition hover:border-copper hover:bg-copper/10"
                >
                  <span className="block text-[13px] text-copper">{item.label}</span>
                  <span className="mt-0.5 block text-[11px] text-titanium/60">{item.desc}</span>
                </Link>
              ))}
            </div>
          </section>
        </div>
      </DeptV2PageShell>
    </ConsoleProvider>
  );
}
