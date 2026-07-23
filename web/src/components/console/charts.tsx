"use client";

import { cn } from "@/lib/utils";

// ─── Sparkline ───────────────────────────────────────────────────────────────
export function Sparkline({
  data,
  width = 120,
  height = 36,
  stroke = "#B87333",
  fill = true,
  strokeWidth = 1.5,
  className,
}: {
  data: number[];
  width?: number;
  height?: number;
  stroke?: string;
  fill?: boolean;
  strokeWidth?: number;
  className?: string;
}) {
  if (data.length === 0) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const stepX = width / (data.length - 1 || 1);
  const points = data.map((v, i) => {
    const x = i * stepX;
    const y = height - ((v - min) / range) * (height - 4) - 2;
    return [x, y] as const;
  });
  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p[0]} ${p[1]}`).join(" ");
  const areaPath = `${linePath} L ${width} ${height} L 0 ${height} Z`;
  const gid = `spark-${Math.round(stroke.charCodeAt(1) * 31 + data[0])}`;
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className={className} preserveAspectRatio="none">
      {fill && (
        <>
          <defs>
            <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={stroke} stopOpacity="0.35" />
              <stop offset="100%" stopColor={stroke} stopOpacity="0" />
            </linearGradient>
          </defs>
          <path d={areaPath} fill={`url(#${gid})`} />
        </>
      )}
      <path d={linePath} fill="none" stroke={stroke} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={points[points.length - 1][0]} cy={points[points.length - 1][1]} r="2" fill={stroke} />
    </svg>
  );
}

// ─── Donut / Ring ────────────────────────────────────────────────────────────
export function Donut({
  segments,
  size = 96,
  thickness = 10,
  centerLabel,
  centerValue,
  className,
}: {
  segments: { value: number; color: string }[];
  size?: number;
  thickness?: number;
  centerLabel?: string;
  centerValue?: string;
  className?: string;
}) {
  const total = segments.reduce((s, x) => s + x.value, 0) || 1;
  const radius = (size - thickness) / 2;
  const circ = 2 * Math.PI * radius;
  // pre-compute each segment's dash offset (cumulative) without reassignment
  const segs = segments.reduce<Array<{ color: string; len: number; offset: number }>>(
    (list, s) => {
      const len = (s.value / total) * circ;
      const prev = list.length > 0 ? list[list.length - 1] : null;
      const offset = prev ? prev.offset + prev.len : 0;
      return [...list, { color: s.color, len, offset }];
    },
    []
  );
  return (
    <div className={cn("relative inline-flex items-center justify-center", className)} style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#1a1a1a" strokeWidth={thickness} />
        {segs.map((s, i) => (
          <circle
            key={i}
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={s.color}
            strokeWidth={thickness}
            strokeDasharray={`${s.len} ${circ - s.len}`}
            strokeDashoffset={-s.offset}
            strokeLinecap="butt"
          />
        ))}
      </svg>
      {(centerValue || centerLabel) && (
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {centerValue && <span className="text-lg font-bold text-ivoire leading-none">{centerValue}</span>}
          {centerLabel && <span className="text-[9px] uppercase tracking-wide text-titane/60 mt-1">{centerLabel}</span>}
        </div>
      )}
    </div>
  );
}

// ─── Vertical bars ───────────────────────────────────────────────────────────
export function Bars({
  data,
  height = 80,
  color = "#B87333",
  className,
}: {
  data: { label: string; value: number }[];
  height?: number;
  color?: string;
  className?: string;
}) {
  const max = Math.max(...data.map((d) => d.value), 1);
  return (
    <div className={cn("flex items-end gap-1.5", className)} style={{ height }}>
      {data.map((d, i) => {
        const h = (d.value / max) * (height - 18);
        const isLast = i === data.length - 1;
        return (
          <div key={`${i}-${d.label}`} className="flex-1 flex flex-col items-center gap-1 group min-w-0">
            <span className="text-[9px] tabular-nums text-titane/50 group-hover:text-bronze-bright transition-colors">
              {d.value}
            </span>
            <div
              className="w-full rounded-t-sm transition-all group-hover:opacity-100"
              style={{
                height: Math.max(2, h),
                background: isLast
                  ? `linear-gradient(180deg, ${color}, ${color}88)`
                  : `linear-gradient(180deg, ${color}55, ${color}22)`,
              }}
            />
            <span className="text-[9px] text-titane/50 truncate w-full text-center">{d.label}</span>
          </div>
        );
      })}
    </div>
  );
}

// ─── Radial gauge ───────────────────────────────────────────────────────────
export function Gauge({
  value,
  max = 100,
  size = 84,
  thickness = 7,
  label,
  unit,
  color = "#B87333",
}: {
  value: number;
  max?: number;
  size?: number;
  thickness?: number;
  label: string;
  unit?: string;
  color?: string;
}) {
  const pct = Math.min(1, value / max);
  const radius = (size - thickness) / 2;
  const circ = 2 * Math.PI * radius;
  const arc = 0.75; // 270° gauge
  const dash = arc * circ;
  const filled = pct * dash;
  const warn = pct > 0.8;
  const c = warn ? "#ffa500" : color;
  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="rotate-[135deg]">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#1a1a1a"
            strokeWidth={thickness}
            strokeDasharray={`${dash} ${circ - dash}`}
            strokeLinecap="round"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={c}
            strokeWidth={thickness}
            strokeDasharray={`${filled} ${circ - filled}`}
            strokeLinecap="round"
            style={{ transition: "stroke-dasharray 0.6s ease-out" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-base font-bold text-ivoire leading-none tabular-nums">{value}{unit && <span className="text-[10px] text-titane/60 ml-0.5">{unit}</span>}</span>
        </div>
      </div>
      <span className="text-[10px] uppercase tracking-wide text-titane/60 text-center leading-tight">{label}</span>
    </div>
  );
}

// ─── Heatmap (7×24) ─────────────────────────────────────────────────────────
export function Heatmap({
  data,
  days,
  color = "#B87333",
  className,
}: {
  data: number[][];
  days: string[];
  color?: string;
  className?: string;
}) {
  return (
    <div className={cn("flex gap-1.5", className)}>
      <div className="flex flex-col gap-1 justify-around pr-1">
        {days.map((d) => (
          <span key={d} className="text-[9px] text-titane/45 leading-none h-3 flex items-center">{d}</span>
        ))}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex gap-[2px]">
          {data[0].map((_, h) => (
            <span key={h} className="flex-1 text-[8px] text-titane/30 text-center">
              {h % 6 === 0 ? `${h}h` : ""}
            </span>
          ))}
        </div>
        <div className="flex flex-col gap-[2px] mt-1">
          {data.map((row, d) => (
            <div key={d} className="flex gap-[2px]">
              {row.map((v, h) => {
                const op = v / 100;
                return (
                  <div
                    key={h}
                    className="flex-1 aspect-square rounded-[2px] min-w-0"
                    style={{
                      background: color,
                      opacity: 0.08 + op * 0.92,
                    }}
                    title={`${days[d]} ${h}h — ${v}`}
                  />
                );
              })}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Agent communication graph ──────────────────────────────────────────────
export function CommGraph({
  edges,
  size = 280,
  className,
}: {
  edges: { from: string; to: string; weight: number }[];
  size?: number;
  className?: string;
}) {
  // Collect unique nodes
  const nodeNames = Array.from(new Set(edges.flatMap((e) => [e.from, e.to])));
  const n = nodeNames.length;
  // Arrange in a circle
  const cx = size / 2;
  const cy = size / 2;
  const r = size / 2 - 28;
  const nodes = nodeNames.map((name, i) => {
    const angle = (i / n) * Math.PI * 2 - Math.PI / 2;
    // Round: server and client float math differ in the last digits, which
    // triggered React hydration mismatches on these SVG coordinates.
    return {
      name,
      x: Number((cx + r * Math.cos(angle)).toFixed(2)),
      y: Number((cy + r * Math.sin(angle)).toFixed(2)),
    };
  });
  const pos = (name: string) => nodes.find((x) => x.name === name)!;
  const maxW = Math.max(...edges.map((e) => e.weight));
  return (
    <svg width="100%" viewBox={`0 0 ${size} ${size}`} className={className}>
      {/* edges */}
      {edges.map((e, i) => {
        const a = pos(e.from);
        const b = pos(e.to);
        const w = e.weight / maxW;
        return (
          <line
            key={i}
            x1={a.x}
            y1={a.y}
            x2={b.x}
            y2={b.y}
            stroke="#B87333"
            strokeOpacity={0.12 + w * 0.35}
            strokeWidth={0.4 + w * 1.4}
          />
        );
      })}
      {/* nodes */}
      {nodes.map((nd) => (
        <g key={nd.name}>
          <circle cx={nd.x} cy={nd.y} r="5" fill="#111111" stroke="#B87333" strokeWidth="1.2" />
          <circle cx={nd.x} cy={nd.y} r="2" fill="#B87333" />
          <text
            x={nd.x}
            y={nd.y - 9}
            textAnchor="middle"
            className="fill-titane/70"
            style={{ fontSize: 7, fontWeight: 600 }}
          >
            {nd.name.length > 10 ? nd.name.slice(0, 9) + "…" : nd.name}
          </text>
        </g>
      ))}
    </svg>
  );
}

// ─── Horizontal capability bar ──────────────────────────────────────────────
export function LevelBar({ value, max = 100, color = "#B87333" }: { value: number; max?: number; color?: string }) {
  const pct = (value / max) * 100;
  return (
    <div className="h-1.5 rounded-full bg-obsidian-deep overflow-hidden">
      <div
        className="h-full rounded-full"
        style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${color}, ${color}aa)` }}
      />
    </div>
  );
}
