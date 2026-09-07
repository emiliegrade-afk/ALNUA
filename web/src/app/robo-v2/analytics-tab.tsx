"use client";

import { useEffect, useState } from "react";
import { fetchLatestRoboTelemetry } from "@/lib/robo-telemetry";
import { fetchRoboLabTests } from "@/lib/robo-lab-tests";
import type { Project, RoboTelemetry } from "@/lib/types";
import { C } from "../app-v2/shared";

/* Analytics Robotique — 100 % Hub-side :
 * énergie/thermique = dernière télémétrie ; tests = lab réel ;
 * manufacturing (fiabilité/unités/défauts) = « — » (pas de système). */

function Tile({
  label,
  value,
  unit,
  warn,
  empty,
}: {
  label: string;
  value: number | string;
  unit?: string;
  warn?: boolean;
  empty?: boolean;
}) {
  return (
    <div
      className="relative rounded-xl border p-3 text-center"
      style={{ borderColor: C.line, background: "#000000", opacity: empty ? 0.75 : 1 }}
    >
      {empty ? (
        <span
          className="absolute right-1.5 top-1.5 rounded px-1 py-0.5 text-[7px] font-bold uppercase tracking-wider"
          style={{ color: C.faint, background: "rgba(255,255,255,0.04)" }}
        >
          N/A
        </span>
      ) : null}
      <p className="text-[19px] font-semibold" style={{ color: warn ? "#f87171" : C.ivory }}>
        {value}
        {unit && value !== "—" ? (
          <span className="text-[11px]" style={{ color: C.faint }}>
            {unit}
          </span>
        ) : null}
      </p>
      <p className="text-[8.5px]" style={{ color: C.faint }}>
        {label}
      </p>
    </div>
  );
}

export function AnalyticsTab({ projects }: { projects: Project[] }) {
  const [telemetry, setTelemetry] = useState<RoboTelemetry | null>(null);
  const [testsPassed, setTestsPassed] = useState<number | null>(null);
  const projectId = projects[0]?.id;

  useEffect(() => {
    if (!projectId) return;
    let cancelled = false;
    fetchLatestRoboTelemetry(projectId).then((t) => {
      if (!cancelled) setTelemetry(t);
    });
    fetchRoboLabTests(projectId).then((tests) => {
      if (cancelled || tests.length === 0) return;
      const decided = tests.filter((t) => t.status !== "in_progress");
      if (decided.length === 0) return;
      const passed = decided.filter((t) => t.status === "pass").length;
      setTestsPassed(Math.round((passed / decided.length) * 100));
    });
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto pb-2">
      <section>
        <p className="mb-2 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
          ÉNERGIE &amp; THERMIQUE
          {!telemetry ? (
            <span className="ml-2" style={{ color: C.dim }}>
              · aucune télémétrie
            </span>
          ) : null}
        </p>
        <div className="grid grid-cols-3 gap-2.5 lg:grid-cols-6">
          <Tile
            label="Consommation"
            value={telemetry?.power_w ?? "—"}
            unit={telemetry?.power_w != null ? "W" : undefined}
            empty={telemetry?.power_w == null}
          />
          <Tile
            label="Température"
            value={telemetry?.temperature_c ?? "—"}
            unit={telemetry?.temperature_c != null ? "°C" : undefined}
            warn={(telemetry?.temperature_c ?? 0) > 55}
            empty={telemetry?.temperature_c == null}
          />
          <Tile
            label="CPU"
            value={telemetry?.cpu_pct ?? "—"}
            unit={telemetry?.cpu_pct != null ? "%" : undefined}
            warn={(telemetry?.cpu_pct ?? 0) > 85}
            empty={telemetry?.cpu_pct == null}
          />
          <Tile
            label="Batterie"
            value={telemetry?.battery_pct ?? "—"}
            unit={telemetry?.battery_pct != null ? "%" : undefined}
            warn={telemetry?.battery_pct != null && telemetry.battery_pct < 50}
            empty={telemetry?.battery_pct == null}
          />
          <Tile
            label="Cycles de charge"
            value={telemetry?.charge_cycles ?? "—"}
            empty={telemetry?.charge_cycles == null}
          />
          <Tile
            label="Autonomie"
            value={telemetry?.autonomy_hours ?? "—"}
            unit={telemetry?.autonomy_hours != null ? "h" : undefined}
            empty={telemetry?.autonomy_hours == null}
          />
        </div>
      </section>

      <section>
        <p className="mb-2 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
          FIABILITÉ &amp; TESTS
        </p>
        <div className="grid grid-cols-2 gap-2.5 lg:grid-cols-4">
          <Tile
            label="Tests lab passés"
            value={testsPassed ?? "—"}
            unit={testsPassed != null ? "%" : undefined}
            empty={testsPassed == null}
          />
          <Tile label="Fiabilité manufacturing" value="—" empty />
          <Tile label="Unités produites" value="—" empty />
          <Tile label="Défauts détectés" value="—" empty />
        </div>
        <p className="mt-2 text-[8.5px]" style={{ color: C.faint }}>
          Manufacturing non branché — pas de chiffres inventés. Lab = essais
          rapportés via /robo/lab-tests.
        </p>
      </section>
    </div>
  );
}
