"use client";

import { useId, useMemo } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const MONTHS = ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun", "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"];

const EVOLUTION_DATA = MONTHS.map((mois, i) => ({
  mois,
  entrees: [22, 28, 26, 34, 48, 42, 55, 62, 58, 70, 78, 85][i] * 1000,
  sorties: [18, 22, 30, 28, 35, 40, 38, 45, 50, 48, 55, 58][i] * 1000,
  profit: [8, 12, 6, 18, 22, 15, 28, 32, 25, 38, 42, 48][i] * 1000,
  invest: [5, 8, 12, 10, 16, 14, 20, 18, 24, 22, 28, 30][i] * 1000,
}));

const SERIES = [
  { key: "entrees", name: "Entrées", color: "#3DDC97" },
  { key: "sorties", name: "Sorties", color: "#FF6B6B" },
  { key: "profit", name: "Profit", color: "#F5C542" },
  { key: "invest", name: "Investissements", color: "#A78BFA" },
] as const;

const EXPENSE_DATA = [
  { name: "SaaS & IA", value: 42, amount: "11 936 €", color: "#C08A72" },
  { name: "Marketing", value: 18, amount: "5 116 €", color: "#E8A87C" },
  { name: "Salaires", value: 16, amount: "4 547 €", color: "#B8C0CC" },
  { name: "R&D", value: 10, amount: "2 842 €", color: "#7C8A9A" },
  { name: "Infrastructure", value: 8, amount: "2 274 €", color: "#5A6570" },
  { name: "Autres", value: 6, amount: "1 705 €", color: "#3D4550" },
];

const tooltipStyle: React.CSSProperties = {
  background: "rgba(14,16,20,0.95)",
  border: "1px solid rgba(192,138,114,0.4)",
  borderRadius: 10,
  fontSize: 11,
  color: "#F5F2EA",
  boxShadow: "0 12px 32px rgba(0,0,0,0.55)",
  backdropFilter: "blur(8px)",
};

function formatEuro(v: number): string {
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(v);
}

/** Filtre glow néon — rendu type maquette ChatGPT. */
function ChartGlowDefs({
  uid,
  colors,
}: {
  uid: string;
  colors: readonly { key: string; color: string }[];
}) {
  return (
    <defs>
      {colors.map((s) => (
        <filter
          key={s.key}
          id={`glow-${uid}-${s.key}`}
          x="-60%"
          y="-60%"
          width="220%"
          height="220%"
        >
          <feGaussianBlur stdDeviation="3.5" result="blur" />
          <feFlood floodColor={s.color} floodOpacity="0.55" result="color" />
          <feComposite in="color" in2="blur" operator="in" result="glow" />
          <feMerge>
            <feMergeNode in="glow" />
            <feMergeNode in="glow" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      ))}
      {colors.map((s) => (
        <linearGradient key={`g-${s.key}`} id={`area-${uid}-${s.key}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={s.color} stopOpacity={0.22} />
          <stop offset="100%" stopColor={s.color} stopOpacity={0} />
        </linearGradient>
      ))}
    </defs>
  );
}

export function FinanceEvolutionChart() {
  const uid = useId().replace(/:/g, "");

  return (
    <div className="relative h-[200px] w-full">
      {/* Soft vignette derrière le chart */}
      <div
        className="pointer-events-none absolute inset-0 rounded-md opacity-40"
        style={{
          background:
            "radial-gradient(ellipse at 40% 60%, rgba(192,138,114,0.08) 0%, transparent 65%)",
        }}
      />
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={EVOLUTION_DATA} margin={{ top: 20, right: 10, left: 0, bottom: 2 }}>
          <ChartGlowDefs uid={uid} colors={SERIES} />
          <CartesianGrid stroke="rgba(255,255,255,0.04)" strokeDasharray="4 6" vertical={false} />
          <XAxis
            dataKey="mois"
            tick={{ fill: "#7A808A", fontSize: 10, fontWeight: 500 }}
            axisLine={{ stroke: "rgba(255,255,255,0.05)" }}
            tickLine={false}
            dy={4}
          />
          <YAxis
            tick={{ fill: "#7A808A", fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            width={38}
            tickFormatter={(v) =>
              new Intl.NumberFormat("fr-FR", { notation: "compact", maximumFractionDigits: 0 }).format(v)
            }
          />
          <Tooltip
            contentStyle={tooltipStyle}
            labelStyle={{ color: "#A7ADB5", marginBottom: 6, fontWeight: 600 }}
            formatter={(value, name) => [formatEuro(Number(value ?? 0)), String(name)]}
            cursor={{ stroke: "rgba(192,138,114,0.25)", strokeWidth: 1 }}
          />
          <Legend
            verticalAlign="top"
            align="right"
            wrapperStyle={{ fontSize: 10, top: -6, fontWeight: 500 }}
            iconType="circle"
            iconSize={8}
          />
          {/* Soft fills sous chaque courbe */}
          {SERIES.map((s) => (
            <Area
              key={`area-${s.key}`}
              type="monotone"
              dataKey={s.key}
              stroke="none"
              fill={`url(#area-${uid}-${s.key})`}
              fillOpacity={1}
              legendType="none"
              tooltipType="none"
              isAnimationActive={false}
            />
          ))}
          {SERIES.map((s) => (
            <Line
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.name}
              stroke={s.color}
              strokeWidth={2.6}
              filter={`url(#glow-${uid}-${s.key})`}
              dot={{
                r: 4,
                fill: "#0B0D11",
                stroke: s.color,
                strokeWidth: 2.2,
              }}
              activeDot={{
                r: 6,
                fill: "#0B0D11",
                stroke: s.color,
                strokeWidth: 2.5,
                style: { filter: `drop-shadow(0 0 8px ${s.color})` },
              }}
              animationDuration={1100}
              animationEasing="ease-out"
            />
          ))}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ExpenseDonut() {
  const uid = useId().replace(/:/g, "");
  const total = 28420;

  return (
    <div className="flex h-full min-h-[190px] items-center gap-3">
      <div className="relative h-[156px] w-[156px] shrink-0">
        {/* Halo derrière le donut */}
        <div
          className="pointer-events-none absolute inset-3 rounded-full opacity-50"
          style={{
            background: "radial-gradient(circle, rgba(192,138,114,0.2) 0%, transparent 70%)",
            filter: "blur(8px)",
          }}
        />
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <defs>
              <filter id={`donut-glow-${uid}`} x="-30%" y="-30%" width="160%" height="160%">
                <feGaussianBlur stdDeviation="1.8" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>
            <Pie
              data={EXPENSE_DATA}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={48}
              outerRadius={70}
              paddingAngle={3}
              stroke="#0B0D11"
              strokeWidth={2}
              filter={`url(#donut-glow-${uid})`}
              animationDuration={900}
              animationBegin={100}
            >
              {EXPENSE_DATA.map((entry) => (
                <Cell key={entry.name} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={tooltipStyle}
              formatter={(value, name) => [`${value}%`, String(name)]}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <p className="font-title text-[15px] font-semibold tracking-wide text-ivoire drop-shadow-[0_0_8px_rgba(192,138,114,0.35)]">
            {formatEuro(total)}
          </p>
          <p className="text-[9px] uppercase tracking-[0.14em] text-titane/45">total</p>
        </div>
      </div>
      <div className="min-w-0 flex-1 space-y-1.5">
        {EXPENSE_DATA.map((e) => (
          <div key={e.name} className="flex items-center justify-between gap-2 text-[10px]">
            <span className="flex min-w-0 items-center gap-1.5 text-titane/70">
              <span
                className="h-2 w-2 shrink-0 rounded-full shadow-[0_0_6px_currentColor]"
                style={{ background: e.color, color: e.color }}
              />
              <span className="truncate">{e.name}</span>
            </span>
            <span className="shrink-0 tabular-nums">
              <span className="font-semibold text-ivoire/90">{e.value}%</span>
              <span className="text-titane/35"> · {e.amount}</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/** Sparkline glow — utilisé en fond des KPI / scénarios. */
export function MiniTrend({
  values,
  color,
  thick,
}: {
  values: number[];
  color: string;
  /** Version plus épaisse pour cartes prévisions. */
  thick?: boolean;
}) {
  const uid = useId().replace(/:/g, "");
  const data = useMemo(() => values.map((v, i) => ({ i, v })), [values]);

  return (
    <div className="h-full min-h-[32px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id={`spark-fill-${uid}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={thick ? 0.65 : 0.5} />
              <stop offset="55%" stopColor={color} stopOpacity={0.18} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
            <filter id={`spark-glow-${uid}`} x="-40%" y="-40%" width="180%" height="180%">
              <feGaussianBlur stdDeviation={thick ? 2.4 : 1.8} result="blur" />
              <feFlood floodColor={color} floodOpacity="0.45" result="color" />
              <feComposite in="color" in2="blur" operator="in" result="glow" />
              <feMerge>
                <feMergeNode in="glow" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <Area
            type="monotone"
            dataKey="v"
            stroke={color}
            strokeWidth={thick ? 2.6 : 2.1}
            fill={`url(#spark-fill-${uid})`}
            filter={`url(#spark-glow-${uid})`}
            dot={false}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

/** Barres glow pour scénarios de trésorerie (aspect maquette). */
export function ForecastBars({
  color,
  values,
}: {
  color: string;
  values: number[];
}) {
  const uid = useId().replace(/:/g, "");
  const data = useMemo(() => values.map((v, i) => ({ i, v })), [values]);

  return (
    <div className="h-12 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 2, right: 0, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id={`bar-${uid}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.95} />
              <stop offset="100%" stopColor={color} stopOpacity={0.25} />
            </linearGradient>
            <filter id={`bar-glow-${uid}`} x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="2" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <Bar
            dataKey="v"
            fill={`url(#bar-${uid})`}
            filter={`url(#bar-glow-${uid})`}
            radius={[3, 3, 0, 0]}
            isAnimationActive={false}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export const EXPENSES = EXPENSE_DATA;
