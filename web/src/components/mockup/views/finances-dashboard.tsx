"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowDownRight, ArrowUpRight, TrendingUp, Wallet } from "lucide-react";
import { cn } from "@/lib/utils";
import { MockCard, ProgressBar } from "../mockup-widgets";
import {
  ExpenseDonut,
  FinanceEvolutionChart,
  ForecastBars,
  MiniTrend,
} from "./finances-charts";
import {
  FINANCES_BUDGETS,
  FINANCES_DEADLINES,
  FINANCES_INVESTMENTS,
  FINANCES_KPIS,
  FINANCES_SUBSCRIPTIONS,
  FINANCES_TRANSACTIONS,
} from "./finances-data";
import type { FinancesTab } from "./finances-data";

interface FinancesDashboardProps {
  onNavigateTab: (tab: FinancesTab) => void;
}

const fadeUp = {
  hidden: { opacity: 0, y: 10 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.04, duration: 0.3, ease: [0.22, 1, 0.36, 1] as const },
  }),
};

/** Maquette : 4 cards alignées sur grand écran (≥1536px), stack droite sinon. */
export function FinancesDashboard({ onNavigateTab }: FinancesDashboardProps) {
  return (
    <div className="flex flex-col gap-2.5">
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-6">
        {FINANCES_KPIS.map((k, i) => {
          const clickable = k.tab !== null;
          const Tag = clickable ? "button" : "div";
          return (
            <motion.div key={k.label} custom={i} variants={fadeUp} initial="hidden" animate="show">
              <Tag
                type={clickable ? "button" : undefined}
                onClick={clickable ? () => onNavigateTab(k.tab!) : undefined}
                className={cn(
                  "relative flex h-full min-h-[92px] w-full flex-col overflow-hidden rounded-lg border border-bronze-faint bg-[#12151b]/95 p-2.5 pb-10 text-left transition-all duration-300",
                  clickable &&
                    "cursor-pointer hover:-translate-y-0.5 hover:border-copper/40 hover:shadow-[0_0_18px_rgba(192,138,114,0.12)]",
                )}
              >
                <p className="relative z-10 text-[8px] font-medium uppercase tracking-[0.18em] text-titane/50">
                  {k.label}
                </p>
                <p className="relative z-10 mt-1 font-title text-[15px] font-semibold leading-none tracking-wide text-ivoire sm:text-base">
                  {k.value}
                </p>
                <div className="relative z-10 mt-1 flex items-center gap-0.5 text-[10px]">
                  {k.deltaType === "up" ? (
                    <ArrowUpRight className="h-3 w-3 text-online" />
                  ) : k.deltaType === "down" ? (
                    <ArrowDownRight className="h-3 w-3 text-orange-400" />
                  ) : null}
                  <span
                    className={cn(
                      "font-medium",
                      k.deltaType === "up" && "text-online",
                      k.deltaType === "down" && "text-orange-400",
                      k.deltaType === "neutral" && "text-titane/55",
                    )}
                  >
                    {k.delta}
                  </span>
                </div>
                {/* Sparkline en fond bas de carte — aspect maquette */}
                <div className="pointer-events-none absolute inset-x-0 bottom-0 h-11 opacity-90">
                  <MiniTrend values={k.trend} color={k.color} />
                </div>
              </Tag>
            </motion.div>
          );
        })}
      </div>

      {/* 2xl = 4 cards alignées ; xl = 3 (Échéances+Abonnements empilés) */}
      <div className="grid grid-cols-1 gap-2.5 xl:grid-cols-12 xl:items-stretch">
        <motion.div className="xl:col-span-5 2xl:col-span-5" custom={6} variants={fadeUp} initial="hidden" animate="show">
          <MockCard
            className="h-full !rounded-lg bg-[#12151b]/95"
            dense
            title="ÉVOLUTION FINANCIÈRE"
            action={<TrendingUp className="h-3.5 w-3.5 text-copper/70" />}
          >
            <FinanceEvolutionChart />
          </MockCard>
        </motion.div>

        <motion.div className="xl:col-span-4 2xl:col-span-3" custom={7} variants={fadeUp} initial="hidden" animate="show">
          <MockCard
            className="h-full !rounded-lg bg-[#12151b]/95"
            dense
            title="RÉPARTITION DES DÉPENSES"
            action={<Wallet className="h-3.5 w-3.5 text-copper/70" />}
          >
            <ExpenseDonut />
          </MockCard>
        </motion.div>

        {/* Sur 2xl : 2 cards côte à côte ; sinon stack */}
        <div className="grid grid-cols-1 gap-2.5 xl:col-span-3 2xl:col-span-4 2xl:grid-cols-2">
          <motion.div className="min-h-0" custom={8} variants={fadeUp} initial="hidden" animate="show">
            <MockCard
              className="h-full !rounded-lg bg-[#12151b]/95"
              dense
              title="PROCHAINS ÉCHÉANCES"
              action={<SeeAll onClick={() => onNavigateTab("Fiscalité")} />}
            >
              <div className="space-y-1.5">
                {FINANCES_DEADLINES.map((d) => (
                  <div key={d.label} className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="truncate text-[11px] text-ivoire/85">{d.label}</p>
                      <p className="text-[9px] text-copper">Dans {d.days} jours</p>
                    </div>
                    <span className="shrink-0 text-[11px] font-medium text-ivoire/80">{d.amount}</span>
                  </div>
                ))}
              </div>
            </MockCard>
          </motion.div>

          <motion.div className="min-h-0" custom={9} variants={fadeUp} initial="hidden" animate="show">
            <MockCard
              className="h-full !rounded-lg bg-[#12151b]/95"
              dense
              title="ABONNEMENTS & SAAS"
              action={<SeeAll onClick={() => onNavigateTab("Facturation")} />}
            >
              <div className="space-y-1.5">
                {FINANCES_SUBSCRIPTIONS.map((s) => (
                  <div key={s.name} className="flex items-center justify-between gap-2">
                    <div className="flex min-w-0 items-center gap-2">
                      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-obsidian text-[8px] font-bold text-copper">
                        {s.name.slice(0, 2).toUpperCase()}
                      </span>
                      <span className="truncate text-[11px] text-ivoire/85">{s.name}</span>
                    </div>
                    <div className="flex shrink-0 items-center gap-1.5">
                      <span className="text-[10px] text-titane/60">{s.cost}</span>
                      <span className="rounded-full bg-online/10 px-1.5 py-0.5 text-[9px] text-online">Actif</span>
                    </div>
                  </div>
                ))}
              </div>
            </MockCard>
          </motion.div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-2.5 xl:grid-cols-12 xl:items-stretch">
        <motion.div className="xl:col-span-5 2xl:col-span-5" custom={10} variants={fadeUp} initial="hidden" animate="show">
          <MockCard
            className="h-full !rounded-lg bg-[#12151b]/95"
            dense
            title="BUDGETS PAR DÉPARTEMENT"
            action={<SeeAll onClick={() => onNavigateTab("Budgets")} />}
          >
            <div className="overflow-x-auto">
              <table className="w-full text-left text-[11px]">
                <thead>
                  <tr className="text-[9px] uppercase tracking-wider text-titane/45">
                    <th className="pb-2 font-medium">Département</th>
                    <th className="pb-2 font-medium">Budget</th>
                    <th className="pb-2 font-medium">Dépensé</th>
                    <th className="pb-2 font-medium">Restant</th>
                    <th className="pb-2 font-medium">Avancement</th>
                  </tr>
                </thead>
                <tbody>
                  {FINANCES_BUDGETS.map((b) => {
                    const remaining = b.budget - b.spent;
                    const pct = Math.round((b.spent / b.budget) * 100);
                    return (
                      <tr
                        key={b.dept}
                        className="border-t border-bronze-faint/50 transition-colors hover:bg-copper/5"
                      >
                        <td className="py-1.5">
                          <Link href={b.href} className="font-medium text-ivoire/90 hover:text-copper">
                            {b.dept}
                          </Link>
                        </td>
                        <td className="py-1.5 text-titane/70">{b.budget} k€</td>
                        <td className="py-1.5 text-titane/70">{b.spent} k€</td>
                        <td className="py-1.5 text-titane/70">{remaining} k€</td>
                        <td className="py-1.5">
                          <div className="flex items-center gap-2">
                            <ProgressBar value={pct} className="min-w-[56px]" />
                            <span className="w-8 text-right text-copper">{pct}%</span>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </MockCard>
        </motion.div>

        <motion.div className="xl:col-span-4 2xl:col-span-3" custom={11} variants={fadeUp} initial="hidden" animate="show">
          <MockCard
            className="h-full !rounded-lg bg-[#12151b]/95"
            dense
            title="PRÉVISIONS DE TRÉSORERIE"
            action={<SeeAll onClick={() => onNavigateTab("Prévisions")} />}
          >
            <div className="grid h-full grid-cols-3 gap-2">
              <ForecastCard label="Scénario actuel" value="62 340 €" trend={[40, 48, 52, 58, 55, 62]} color="#A7ADB5" />
              <ForecastCard
                label="Optimiste +30%"
                value="71 200 €"
                trend={[35, 42, 50, 58, 65, 72]}
                color="#3DDC97"
                arrow="up"
              />
              <ForecastCard
                label="Pessimiste -25%"
                value="54 800 €"
                trend={[62, 58, 54, 50, 48, 44]}
                color="#FF6B6B"
                arrow="down"
              />
            </div>
          </MockCard>
        </motion.div>

        <div className="grid grid-cols-1 gap-2.5 xl:col-span-3 2xl:col-span-4 2xl:grid-cols-2">
          <motion.div className="min-h-0" custom={12} variants={fadeUp} initial="hidden" animate="show">
            <MockCard
              className="h-full !rounded-lg bg-[#12151b]/95"
              dense
              title="DERNIÈRES TRANSACTIONS"
              action={<SeeAll onClick={() => onNavigateTab("Transactions")} />}
            >
              <div className="space-y-1.5">
                {FINANCES_TRANSACTIONS.map((t) => (
                  <div key={t.desc} className="flex items-center justify-between gap-2">
                    <div className="min-w-0">
                      <p className="truncate text-[11px] text-ivoire/85">{t.desc}</p>
                      <p className="text-[10px] text-titane/45">{t.date}</p>
                    </div>
                    <span
                      className={cn(
                        "shrink-0 text-[11px] font-medium",
                        t.type === "in" ? "text-online" : "text-red-400",
                      )}
                    >
                      {t.type === "in" ? "+" : ""}
                      {t.amount.toLocaleString("fr-FR")} €
                    </span>
                  </div>
                ))}
              </div>
            </MockCard>
          </motion.div>

          <motion.div className="min-h-0" custom={13} variants={fadeUp} initial="hidden" animate="show">
            <MockCard
              className="h-full !rounded-lg bg-[#12151b]/95"
              dense
              title="INVESTISSEMENTS"
              action={<SeeAll onClick={() => onNavigateTab("Investissements")} />}
            >
              <div className="space-y-1.5">
                {FINANCES_INVESTMENTS.map((inv) => (
                  <div key={inv.name} className="flex items-center justify-between gap-2">
                    <div className="min-w-0">
                      <p className="truncate text-[11px] text-ivoire/85">{inv.name}</p>
                      <p className="text-[10px] text-titane/45">{inv.amount}</p>
                    </div>
                    <span className="shrink-0 text-[11px] font-medium text-online">ROI {inv.roi}</span>
                  </div>
                ))}
              </div>
            </MockCard>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

function SeeAll({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="text-[10px] text-copper transition-colors hover:text-copper-light hover:underline"
    >
      Voir tout →
    </button>
  );
}

function ForecastCard({
  label,
  value,
  trend,
  color,
  arrow,
}: {
  label: string;
  value: string;
  trend: number[];
  color: string;
  arrow?: "up" | "down";
}) {
  return (
    <div className="flex flex-col rounded-lg border border-bronze-faint bg-obsidian/60 p-2 text-center transition-all duration-300 hover:border-copper/30">
      <p className="text-[8px] uppercase tracking-wider text-titane/50">{label}</p>
      <p className="mt-1 font-title text-sm font-semibold text-ivoire">{value}</p>
      {arrow === "up" ? (
        <ArrowUpRight className="mx-auto mt-0.5 h-3 w-3 text-online" />
      ) : arrow === "down" ? (
        <ArrowDownRight className="mx-auto mt-0.5 h-3 w-3 text-red-400" />
      ) : (
        <div className="h-3" />
      )}
      <div className="mt-auto pt-1">
        <ForecastBars values={trend} color={color} />
      </div>
    </div>
  );
}
