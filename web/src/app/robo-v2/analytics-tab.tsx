"use client";

import { useEffect, useState } from "react";
import { fetchLatestRoboTelemetry } from "@/lib/robo-telemetry";
import { fetchRoboLabTests } from "@/lib/robo-lab-tests";
import type { Project, RoboTelemetry } from "@/lib/types";
import { C } from "../app-v2/shared";
import { pct } from "./mock-data";

/* Analytics Robotique — ÉNERGIE & THERMIQUE vient de la dernière télémétrie
 * IoT réelle rapportée (Phase 20, ROADMAP.md, 2026-07-30, robo_telemetry),
 * "—" tant qu'aucune n'a été rapportée (pas encore de capteurs connectés sur
 * Eve). "Tests passés" (FIABILITÉ & TESTS) est calculé sur les vrais essais
 * de Laboratoire (Phase 19) quand il en existe. Fiabilité/Unités produites/
 * Défauts restent provisoires — pas de système de suivi manufacturing. */

function Tile({ label, value, unit, warn }: { label: string; value: number | string; unit?: string; warn?: boolean }) {
  return (
    <div className="rounded-xl border p-3 text-center" style={{ borderColor: C.line, background: "rgba(19,22,27,.55)" }}>
      <p className="text-[19px] font-semibold" style={{ color: warn ? "#f87171" : C.ivory }}>
        {value}
        {unit ? <span className="text-[11px]" style={{ color: C.faint }}>{unit}</span> : null}
      </p>
      <p className="text-[8.5px]" style={{ color: C.faint }}>
        {label}
      </p>
    </div>
  );
}

export function AnalyticsTab({ projects }: { projects: Project[] }) {
  const seed = projects[0]?.id ?? "robo-default";
  const reliability = pct(`${seed}-reliability`, 80, 99);
  const production = pct(`${seed}-production`, 0, 50);
  const defects = pct(`${seed}-defects`, 0, 15);

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
        </p>
        <div className="grid grid-cols-3 gap-2.5 lg:grid-cols-6">
          <Tile label="Consommation" value={telemetry?.power_w ?? "—"} unit={telemetry?.power_w != null ? "W" : ""} />
          <Tile label="Température" value={telemetry?.temperature_c ?? "—"} unit={telemetry?.temperature_c != null ? "°C" : ""} warn={(telemetry?.temperature_c ?? 0) > 55} />
          <Tile label="CPU" value={telemetry?.cpu_pct ?? "—"} unit={telemetry?.cpu_pct != null ? "%" : ""} warn={(telemetry?.cpu_pct ?? 0) > 85} />
          <Tile label="Batterie" value={telemetry?.battery_pct ?? "—"} unit={telemetry?.battery_pct != null ? "%" : ""} warn={telemetry?.battery_pct != null && telemetry.battery_pct < 50} />
          <Tile label="Cycles de charge" value={telemetry?.charge_cycles ?? "—"} />
          <Tile label="Autonomie" value={telemetry?.autonomy_hours ?? "—"} unit={telemetry?.autonomy_hours != null ? "h" : ""} />
        </div>
      </section>

      <section>
        <p className="mb-2 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
          FIABILITÉ &amp; TESTS
        </p>
        <div className="grid grid-cols-2 gap-2.5 lg:grid-cols-4">
          <Tile label="Tests passés" value={testsPassed ?? "—"} unit={testsPassed != null ? "%" : ""} />
          <Tile label="Fiabilité" value={reliability} unit="%" />
          <Tile label="Unités produites" value={production} />
          <Tile label="Défauts détectés" value={defects} warn={defects > 8} />
        </div>
      </section>
    </div>
  );
}
