"use client";

/** Decorative copper-rose HUD chart primitives — inspired by sci-fi monitoring dashboards. */

const COPPER = "#C08A62";
const COPPER_LIGHT = "#D4A882";
const COPPER_GLOW = "rgba(192, 138, 98, 0.35)";

export function HudPanel({
  title,
  children,
  className = "",
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`relative overflow-hidden rounded border border-copper/25 bg-obsidian/40 p-2 ${className}`}
      style={{ boxShadow: `inset 0 0 20px ${COPPER_GLOW}` }}
    >
      <div className="pointer-events-none absolute left-0 top-0 h-2 w-2 border-l border-t border-copper/60" />
      <div className="pointer-events-none absolute right-0 top-0 h-2 w-2 border-r border-t border-copper/60" />
      <p className="mb-1.5 font-body text-[7px] uppercase tracking-[0.25em] text-copper/70">
        {title}
      </p>
      {children}
    </div>
  );
}

export function HudSparkline({ data }: { data: number[] }) {
  const max = Math.max(...data, 1);
  const w = 100;
  const h = 28;
  const pts = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * w;
      const y = h - (v / max) * (h - 4) - 2;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="h-7 w-full" aria-hidden>
      <polyline
        fill="none"
        stroke={COPPER}
        strokeWidth="1.5"
        points={pts}
        style={{ filter: `drop-shadow(0 0 3px ${COPPER})` }}
      />
      <polyline
        fill="none"
        stroke={COPPER_LIGHT}
        strokeWidth="0.8"
        strokeOpacity="0.5"
        points={pts}
        transform="translate(0, 3)"
      />
    </svg>
  );
}

export function HudRingGauge({
  value,
  max,
  label,
}: {
  value: number;
  max: number;
  label: string;
}) {
  const pct = max > 0 ? value / max : 0;
  const r = 18;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - pct);

  return (
    <div className="flex flex-col items-center">
      <svg width="48" height="48" viewBox="0 0 48 48" aria-hidden>
        <circle
          cx="24"
          cy="24"
          r={r}
          fill="none"
          stroke="rgba(192,138,98,0.15)"
          strokeWidth="3"
        />
        <circle
          cx="24"
          cy="24"
          r={r}
          fill="none"
          stroke={COPPER}
          strokeWidth="3"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 24 24)"
          style={{ filter: `drop-shadow(0 0 4px ${COPPER})` }}
        />
        <text
          x="24"
          y="26"
          textAnchor="middle"
          fill={COPPER_LIGHT}
          fontSize="11"
          fontFamily="monospace"
        >
          {value}
        </text>
      </svg>
      <span className="font-body text-[7px] uppercase tracking-wider text-copper/60">
        {label}
      </span>
    </div>
  );
}

export function HudBarChart({
  bars,
}: {
  bars: { label: string; value: number }[];
}) {
  const max = Math.max(...bars.map((b) => b.value), 1);
  return (
    <div className="space-y-1">
      {bars.map((b) => (
        <div key={b.label} className="flex items-center gap-1.5">
          <span className="w-8 shrink-0 truncate font-body text-[6px] text-titanium/50">
            {b.label}
          </span>
          <div className="h-1.5 flex-1 overflow-hidden rounded-sm bg-copper/10">
            <div
              className="h-full rounded-sm bg-gradient-to-r from-copper/60 to-copper"
              style={{
                width: `${(b.value / max) * 100}%`,
                boxShadow: `0 0 6px ${COPPER_GLOW}`,
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

export function HudWaveform() {
  return (
    <svg viewBox="0 0 120 24" className="h-6 w-full" aria-hidden>
      <path
        d="M0,12 Q10,4 20,12 T40,12 T60,12 T80,12 T100,12 T120,12"
        fill="none"
        stroke={COPPER}
        strokeWidth="1.2"
        opacity="0.9"
        style={{ filter: `drop-shadow(0 0 2px ${COPPER})` }}
      />
      <path
        d="M0,14 Q15,20 30,14 T60,14 T90,14 T120,14"
        fill="none"
        stroke={COPPER_LIGHT}
        strokeWidth="0.8"
        opacity="0.4"
      />
    </svg>
  );
}

export function HudHexIcon({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="flex h-8 w-8 items-center justify-center text-copper"
      style={{
        clipPath:
          "polygon(50% 0%, 95% 25%, 95% 75%, 50% 100%, 5% 75%, 5% 25%)",
        background: "rgba(192, 138, 98, 0.12)",
        boxShadow: `inset 0 0 8px ${COPPER_GLOW}`,
      }}
    >
      {children}
    </div>
  );
}
