"use client";

import { ConsoleProvider } from "@/components/console/console-provider";
import { DeptV2PageShell } from "@/components/dept-v2";
import { BureauIdentityStrip } from "@/components/shared/bureau-identity-strip";
import { BureauRoster } from "@/components/shared/bureau-roster";
import { SiegeLifeLinks } from "@/components/shared/siege-life-links";
import { C } from "@/app/app-v2/shared";
import { ROUTES } from "@/lib/routes";
import Link from "next/link";

const OPS = [
  { href: ROUTES.ceo, label: "CEO", desc: "Brief · décisions" },
  { href: ROUTES.secretary, label: "Secrétariat", desc: "Nadia · docs · mails" },
  { href: ROUTES.legal, label: "Juridique", desc: "Solène · contrats" },
  { href: ROUTES.activity, label: "Activité", desc: "Feed live" },
  { href: ROUTES.academy, label: "Académie", desc: "Pipeline agents" },
  { href: ROUTES.trust, label: "Trust", desc: "Fiabilité agents" },
  { href: ROUTES.finances, label: "Finance", desc: "Budget · factures" },
  { href: ROUTES.settings, label: "Réglages", desc: "Modèles · clés" },
] as const;

/** Direction — roster portraits + ops, void (pas de cards grises). */
export default function HubPage() {
  return (
    <ConsoleProvider>
      <DeptV2PageShell deptHref={ROUTES.hub} activeDeptId="hub" coreSubtitle="Direction ops">
        <div
          className="alnua-scroll flex min-w-0 flex-1 flex-col gap-5 overflow-y-auto px-4 pb-4 pt-3.5"
          style={{ color: C.ivory }}
        >
          <header className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h1 className="text-[26px] leading-[1.05] tracking-[1px]">
                <span className="font-bold">DIRECTION</span>{" "}
                <span className="font-light tracking-[0.35em]" style={{ color: C.titanium }}>
                  HUB
                </span>
              </h1>
              <p className="mt-1 text-[12px]" style={{ color: C.dim }}>
                Aria · Sam · Léon · Alex · Hugo — orchestration
              </p>
            </div>
            <SiegeLifeLinks />
          </header>

          <BureauIdentityStrip
            agentId="coo"
            name="Aria Voss"
            role="COO — chef d'orchestre"
            href={ROUTES.ceo}
            hrefLabel="CEO"
          />

          <BureauRoster bureau="hub" title="Équipe Direction" />

          <section className="border border-titanium/20 bg-transparent p-3">
            <p className="mb-3 text-[10px] uppercase tracking-[0.2em] text-titanium/55">
              Accès ops
            </p>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
              {OPS.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="border border-titanium/25 px-3 py-2.5 transition hover:border-copper/50"
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
