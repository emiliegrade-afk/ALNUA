"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { SiegeLifeLinks } from "@/components/shared/siege-life-links";
import {
  DIRECTION_DOCS,
  DIRECTION_LEADS,
} from "@/components/siege/direction-leads";
import {
  SiegeBadge,
  SiegePageHeader,
  SiegePanel,
  SiegeProgress,
} from "@/components/siege/siege-ui";
import { fetchCostAlert } from "@/lib/admin-costs-api";
import { getAgentsForBureau } from "@/lib/agent-bureau";
import { ROUTES } from "@/lib/routes";
import { fetchAgentTrustList, trustPercent } from "@/lib/trust-api";

type LiveKpi = {
  label: string;
  display: string;
  value: number | null;
  href: string;
  hint?: string;
};

/** Direction — KPIs live (trust / coûts) + portraits pôles. Plus de chiffres inventés. */
export function DirectionCommandView() {
  const hubCount = getAgentsForBureau("hub").length;
  const [kpis, setKpis] = useState<LiveKpi[]>([
    { label: "Trust agents", display: "…", value: null, href: ROUTES.trust },
    { label: "Budget LLM (jour)", display: "…", value: null, href: ROUTES.finances },
    {
      label: "Agents Direction",
      display: String(hubCount),
      value: Math.min(100, hubCount * 12),
      href: ROUTES.agents,
      hint: "roster",
    },
  ]);

  useEffect(() => {
    let cancelled = false;
    void Promise.all([
      fetchAgentTrustList(80).catch(() => []),
      fetchCostAlert(5).catch(() => null),
    ]).then(([trustRows, alert]) => {
      if (cancelled) return;
      const avgTrust =
        trustRows.length > 0
          ? Math.round(
              trustRows.reduce((s, r) => s + trustPercent(r.score), 0) /
                trustRows.length,
            )
          : null;
      const budgetPct =
        alert != null ? Math.round(Math.min(100, Math.max(0, alert.pct_used))) : null;
      setKpis([
        {
          label: "Trust agents (moy.)",
          display: avgTrust != null ? `${avgTrust}%` : "—",
          value: avgTrust,
          href: ROUTES.trust,
          hint: trustRows.length ? `${trustRows.length} agents` : "indisponible",
        },
        {
          label: "Budget LLM (jour)",
          display:
            budgetPct != null
              ? `${budgetPct}%`
              : alert
                ? `$${alert.spent_usd.toFixed(2)}`
                : "—",
          value: budgetPct,
          href: ROUTES.finances,
          hint: alert ? alert.severity : "indisponible",
        },
        {
          label: "Agents Direction",
          display: String(hubCount),
          value: Math.min(100, hubCount * 12),
          href: ROUTES.agents,
          hint: "roster local",
        },
      ]);
    });
    return () => {
      cancelled = true;
    };
  }, [hubCount]);

  return (
    <div className="flex flex-col gap-4">
      <SiegePageHeader
        title="DIRECTION"
        accent="HUB"
        subtitle={`Aria · équipe Direction (${hubCount}) · gouvernance pôles`}
        trailing={<SiegeLifeLinks />}
      />

      <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
        {kpis.map((k) => (
          <Link key={k.label} href={k.href} className="block transition hover:opacity-90">
            <SiegePanel className="!p-3">
              <p className="text-[10px] uppercase tracking-wider text-titanium/55">{k.label}</p>
              <div className="mt-2 flex items-end justify-between gap-2">
                <span className="text-lg font-semibold tabular-nums text-ivory">{k.display}</span>
                {k.hint ? (
                  <span className="text-[10px] uppercase tracking-wide text-copper/70">
                    {k.hint}
                  </span>
                ) : null}
              </div>
              {k.value != null ? <SiegeProgress value={k.value} className="mt-2" /> : null}
            </SiegePanel>
          </Link>
        ))}
      </div>

      <SiegePanel title="Équipe de management — pôles">
        <div className="alnua-scroll -mx-1 flex gap-3 overflow-x-auto pb-2 pt-1">
          {DIRECTION_LEADS.map((lead) => (
            <article
              key={lead.dept}
              className="flex w-[148px] shrink-0 flex-col overflow-hidden rounded-xl border border-copper/20 bg-obsidian-deep/80"
            >
              <div className="bg-copper/15 px-2 py-1 text-center text-[10px] font-medium uppercase tracking-[0.14em] text-copper">
                {lead.dept}
              </div>
              <div className="flex flex-1 flex-col items-center gap-2 px-3 py-3">
                <AgentAvatar agentId={lead.agentId} name={lead.name} size={72} ring />
                <div className="text-center">
                  <p className="text-[12px] font-medium leading-tight text-ivory">{lead.name}</p>
                  <p className="mt-0.5 text-[10px] leading-snug text-titanium/60">{lead.role}</p>
                  <p className="mt-1 text-[10px] text-copper/75">{lead.agentsHint}</p>
                </div>
                <Link
                  href={lead.href}
                  className="mt-auto w-full rounded-lg border border-copper/35 py-1.5 text-center text-[10px] text-copper transition hover:bg-copper/15"
                >
                  Voir le département
                </Link>
              </div>
            </article>
          ))}
        </div>
      </SiegePanel>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <SiegePanel title="Raccourcis gouvernance">
          <ul className="space-y-2 text-[12px]">
            <li>
              <Link href={ROUTES.hub} className="text-copper hover:underline">
                Workflows Company OS (ops / ship)
              </Link>
            </li>
            <li>
              <Link href={ROUTES.ceo} className="text-copper hover:underline">
                Bureau CEO — dossiers & validations
              </Link>
            </li>
            <li>
              <Link href={ROUTES.briefing} className="text-copper hover:underline">
                Briefing du jour
              </Link>
            </li>
            <li>
              <Link href={ROUTES.trust} className="text-copper hover:underline">
                Trust & Review Board
              </Link>
            </li>
            <li>
              <Link href={ROUTES.competition} className="text-copper hover:underline">
                Compétition agents
              </Link>
            </li>
          </ul>
        </SiegePanel>

        <SiegePanel title="Documents stratégiques">
          <ul className="space-y-2">
            {DIRECTION_DOCS.map((d) => (
              <li key={d.name}>
                <Link href={d.href} className="text-[12px] text-copper hover:underline">
                  {d.name}
                </Link>
              </li>
            ))}
          </ul>
        </SiegePanel>

        <SiegePanel title="Actions prioritaires">
          <ul className="space-y-2.5">
            <li className="flex items-center justify-between gap-2 text-[12px] text-ivory/85">
              <Link href={ROUTES.ceo} className="min-w-0 truncate hover:text-copper">
                Valider dossiers CEO
              </Link>
              <SiegeBadge tone="danger">Prio</SiegeBadge>
            </li>
            <li className="flex items-center justify-between gap-2 text-[12px] text-ivory/85">
              <Link href={ROUTES.academy} className="min-w-0 truncate hover:text-copper">
                Academy / wake
              </Link>
              <SiegeBadge tone="copper">Prio</SiegeBadge>
            </li>
            <li className="flex items-center justify-between gap-2 text-[12px] text-ivory/85">
              <Link href={ROUTES.activity} className="min-w-0 truncate hover:text-copper">
                Activité live
              </Link>
              <SiegeBadge tone="muted">Suivi</SiegeBadge>
            </li>
          </ul>
        </SiegePanel>
      </div>
    </div>
  );
}
