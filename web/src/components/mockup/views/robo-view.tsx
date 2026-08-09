"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Cpu, Network, Shield } from "lucide-react";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import type { ConsoleDepartment } from "@/lib/console/types";
import { cn } from "@/lib/utils";
import { MockCard, ProgressBar, StatusBadge } from "../mockup-widgets";
import { poleFadeUp } from "../pole-page-shell";
import { PoleKpiRow, SeeAllLink } from "../pole-kpi-row";
import { PoleFilledPanel, PoleListCard, PoleProtoTabs, PoleStatStrip } from "../pole-proto-tabs";

interface RoboViewProps {
  department: ConsoleDepartment;
}

const TABS = [
  { id: "vue", label: "Vue d'ensemble" },
  { id: "prototypes", label: "Prototypes" },
  { id: "firmware", label: "Firmware" },
  { id: "bom", label: "BOM" },
  { id: "tests", label: "Tests" },
  { id: "safety", label: "Safety" },
];

const AGENTS = [
  { id: "hardware", name: "Yuki Tanaka", role: "Hardware Engineer", load: 76, skills: ["PCB", "Sensors", "CAD"] },
  { id: "vision_ai", name: "Sana Okoye", role: "Vision AI", load: 82, skills: ["CV", "Edge ML", "ROS"] },
  { id: "firmware", name: "Petra Vogel", role: "Firmware Lead", load: 69, skills: ["RTOS", "C++", "IoT"] },
  { id: "mechanical", name: "Ravi Chandrasekaran", role: "Mechanical", load: 58, skills: ["CAD", "BOM", "Prototyping"] },
];

const TELEMETRY = [
  { label: "CPU", value: 47, unit: "%" },
  { label: "Mémoire", value: 63, unit: "%" },
  { label: "Batterie", value: 82, unit: "%" },
  { label: "Temp", value: 41, unit: "°C" },
];

const BOM = [
  { item: "Caméra RGB-D", qty: 1, cost: "89€" },
  { item: "MCU STM32H7", qty: 1, cost: "34€" },
  { item: "Motor driver", qty: 4, cost: "48€" },
  { item: "LiDAR 2D", qty: 1, cost: "156€" },
  { item: "Batterie 4S", qty: 1, cost: "72€" },
];

type Row = { primary: string; secondary?: string; meta?: string; tone?: "ok" | "warn" | "muted" };
type Panel = { title: string; subtitle: string; stats: { label: string; value: string }[]; cards: { title: string; rows: Row[] }[] };

const S = (items: [string, string][]) => items.map(([label, value]) => ({ label, value }));
const R = (primary: string, secondary: string, meta: string, tone: Row["tone"] = "muted"): Row => ({
  primary,
  secondary,
  meta,
  tone,
});

const PANELS: Record<string, Panel> = {
  prototypes: {
    title: "Prototypes",
    subtitle: "Hardware Workshop · validation terrain",
    stats: S([["EVE Mark-3", "68%"], ["NOMAD Base", "45%"], ["Sensor Array", "22%"], ["Unités", "3"]]),
    cards: [{
      title: "PROTOTYPES ACTIFS",
      rows: [
        R("EVE Mark-3", "Terrain · ROS 2", "En cours", "warn"),
        R("NOMAD Base", "Châssis + docking", "Prototype", "ok"),
        R("ALUNA Sensor Array", "Multi-capteurs", "Concept", "muted"),
        R("Calibration caméra RGB-D", "Sana · vision · P0", "Next", "warn"),
      ],
    }],
  },
  firmware: {
    title: "Firmware",
    subtitle: "RTOS · STM32H7 · OTA",
    stats: S([["Version", "v0.9.2"], ["OTA prêts", "2"], ["Watchdogs", "OK"], ["Couverture", "81%"]]),
    cards: [{
      title: "RELEASES",
      rows: [
        R("v0.9.2 — motor control", "Petra · 07 août", "Deployed", "ok"),
        R("v0.9.1 — IMU fusion", "Hotfix yaw", "Stable", "ok"),
        R("v0.9.3-rc1 — OTA secure", "Rollback", "En test", "warn"),
      ],
    }],
  },
  bom: {
    title: "BOM EVE Mark-3",
    subtitle: "Coût unitaire · sourcing EU",
    stats: S([["Unitaire", "399€"], ["Lignes", "42"], ["Lead max", "21j"], ["Stock critique", "3"]]),
    cards: [{
      title: "COMPOSANTS CLÉS",
      rows: [
        R("Caméra RGB-D", "Qty 1 · EU", "89€", "ok"),
        R("MCU STM32H7", "DigiKey", "34€", "ok"),
        R("Motor driver ×4", "Stock bas", "48€", "warn"),
        R("LiDAR 2D", "Lead 18j", "156€", "warn"),
      ],
    }],
  },
  tests: {
    title: "Tests",
    subtitle: "Banc HIL · terrain · regression",
    stats: S([["Passés", "38/41"], ["Échoués", "3"], ["Couverture", "76%"], ["HIL runs", "12"]]),
    cards: [{
      title: "DERNIERS RUNS",
      rows: [
        R("Navigation indoor", "EVE · HIL", "Pass", "ok"),
        R("Obstacle stop < 30 cm", "Safety interlock", "Pass", "ok"),
        R("IMU drift 10 min", "Firmware v0.9.2", "Fail", "warn"),
      ],
    }],
  },
  safety: {
    title: "Safety",
    subtitle: "Clara Dubois · conformité terrain",
    stats: S([["Alertes crit.", "0"], ["Uptime field", "99.1%"], ["E-stop", "OK"], ["Incidents 30j", "0"]]),
    cards: [{
      title: "CHECKS SAFETY",
      rows: [
        R("E-stop matériel + logiciel", "Double redondance", "Validé", "ok"),
        R("Limite couple moteurs", "Watchdog FW", "Validé", "ok"),
        R("Zone exclusion LiDAR", "Params Mark-3", "Review", "warn"),
      ],
    }],
  },
};

export function MockupRoboView({ department }: RoboViewProps) {
  void department;
  const [tab, setTab] = useState("vue");
  const panel = PANELS[tab];

  return (
    <div className="space-y-3 pb-6">
      <PoleProtoTabs tabs={TABS} active={tab} onChange={setTab} />
      {tab === "vue" || !panel ? (
        <RoboDashboard onNavigateTab={setTab} />
      ) : (
        <PoleFilledPanel title={panel.title} subtitle={panel.subtitle} onBack={() => setTab("vue")}>
          <PoleStatStrip items={panel.stats} />
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
            {panel.cards.map((c) => (
              <PoleListCard key={c.title} title={c.title} rows={c.rows} />
            ))}
          </div>
        </PoleFilledPanel>
      )}
    </div>
  );
}

function RoboDashboard({ onNavigateTab }: { onNavigateTab: (id: string) => void }) {
  const [selectedId, setSelectedId] = useState(AGENTS[0].id);
  const selected = AGENTS.find((a) => a.id === selectedId) ?? AGENTS[0];

  return (
    <div className="space-y-3">
      <PoleKpiRow
        kpis={[
          { label: "EVE MARK-3", value: "68%", delta: "+4%", deltaType: "up", trend: [52, 56, 60, 63, 65, 68], color: "#C08A72", onClick: () => onNavigateTab("prototypes") },
          { label: "TESTS OK", value: "38/41", delta: "+2", deltaType: "up", trend: [32, 34, 35, 36, 37, 38], color: "#22c55e", onClick: () => onNavigateTab("tests") },
          { label: "FIRMWARE", value: "v0.9.2", delta: "+0.1", deltaType: "up", trend: [0.8, 0.85, 0.87, 0.88, 0.9, 0.92], color: "#60a5fa", onClick: () => onNavigateTab("firmware") },
          { label: "BOM UNIT", value: "399€", delta: "-12€", deltaType: "down", trend: [420, 415, 410, 405, 402, 399], color: "#f97316", onClick: () => onNavigateTab("bom") },
        ]}
      />

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-12">
        <motion.div className="lg:col-span-7" custom={4} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="EVE MARK-3 — PROTOTYPE ACTIF" action={<SeeAllLink onClick={() => onNavigateTab("prototypes")} label="Prototypes" />}>
            <div className="mb-3 flex items-center justify-between rounded-lg border border-copper/30 bg-copper/10 px-3 py-2">
              <div>
                <p className="font-title text-sm font-semibold text-ivoire">EVE Mark-3</p>
                <p className="text-[10px] text-titane/55">Validation terrain · Perception embarquée · ROS 2</p>
              </div>
              <StatusBadge status="active">En validation</StatusBadge>
            </div>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {AGENTS.map((a) => (
                <button
                  key={a.id}
                  type="button"
                  onClick={() => setSelectedId(a.id)}
                  className={cn(
                    "rounded-xl border p-2.5 text-left transition-all hover:border-copper/40",
                    selectedId === a.id ? "border-copper/50 bg-obsidian-2" : "border-bronze-faint bg-obsidian/50",
                  )}
                >
                  <div className="flex items-center gap-2">
                    <AgentAvatar agentId={a.id} name={a.name} size={32} />
                    <div className="min-w-0">
                      <p className="truncate text-[11px] font-medium text-ivoire/90">{a.name.split(" ")[0]}</p>
                      <p className="truncate text-[9px] text-titane/50">{a.role.split(" ")[0]}</p>
                    </div>
                  </div>
                  <div className="mt-2"><ProgressBar value={a.load} /></div>
                </button>
              ))}
            </div>
            <div className="mt-3 rounded-xl border border-bronze-faint bg-obsidian/50 p-3">
              <p className="text-[10px] uppercase tracking-wider text-titane/50">Mission — {selected.name}</p>
              <p className="mt-1 text-[12px] text-ivoire/90">Calibration caméra EVE Mark-3</p>
              <div className="mt-2 flex flex-wrap gap-1">
                {selected.skills.map((s) => (
                  <span key={s} className="rounded-full bg-obsidian-2 px-1.5 py-0.5 text-[9px] text-titane/70">{s}</span>
                ))}
              </div>
            </div>
          </MockCard>
        </motion.div>

        <motion.div className="lg:col-span-5 space-y-3" custom={5} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="TÉLÉMÉTRIE LIVE" action={<Network className="h-3.5 w-3.5 text-copper/70" />}>
            <div className="grid grid-cols-2 gap-2">
              {TELEMETRY.map((t) => (
                <div key={t.label} className="rounded-lg border border-bronze-faint bg-obsidian/50 p-2 text-center">
                  <p className="text-[9px] uppercase tracking-wider text-titane/50">{t.label}</p>
                  <p className="font-title text-base font-semibold text-ivoire">
                    {t.value}<span className="text-[10px]">{t.unit}</span>
                  </p>
                  <ProgressBar value={t.value} />
                </div>
              ))}
            </div>
          </MockCard>
          <MockCard title="SAFETY" action={<Shield className="h-3.5 w-3.5 text-copper/70" />}>
            {[
              { label: "Critical alerts", value: "0" },
              { label: "Uptime field", value: "99.1%" },
              { label: "Cycles batterie", value: "284" },
            ].map((r) => (
              <div key={r.label} className="mb-2 flex items-center justify-between rounded-lg border border-bronze-faint bg-obsidian/50 px-3 py-2">
                <span className="text-[11px] text-titane/65">{r.label}</span>
                <span className="font-title text-sm font-semibold text-ivoire">{r.value}</span>
              </div>
            ))}
            <button type="button" onClick={() => onNavigateTab("safety")} className="w-full text-[10px] text-copper hover:underline">
              Rapport safety →
            </button>
          </MockCard>
        </motion.div>
      </div>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-12">
        <motion.div className="lg:col-span-6" custom={6} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="BOM EVE MARK-3" action={<SeeAllLink onClick={() => onNavigateTab("bom")} label="BOM complète" />}>
            <div className="space-y-2">
              {BOM.map((row) => (
                <div key={row.item} className="flex items-center justify-between rounded-lg border border-bronze-faint bg-obsidian/50 px-3 py-2">
                  <span className="text-[11px] text-ivoire/80">{row.item}</span>
                  <div className="text-right text-[10px] text-titane/55">
                    <span className="mr-2">x{row.qty}</span>
                    <span className="text-copper">{row.cost}</span>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-3 flex items-center justify-between border-t border-bronze-faint pt-2 text-[12px] font-semibold text-ivoire">
              <span>Total unitaire</span>
              <span className="text-copper">399€</span>
            </div>
          </MockCard>
        </motion.div>

        <motion.div className="lg:col-span-6" custom={7} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="AUTRES PROTOTYPES" action={<Cpu className="h-3.5 w-3.5 text-copper/70" />}>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {[
                { name: "NOMAD Base", phase: "Prototype", progress: 45, tests: 12 },
                { name: "ALUNA Sensor Array", phase: "Concept", progress: 22, tests: 5 },
              ].map((p) => (
                <button
                  key={p.name}
                  type="button"
                  onClick={() => onNavigateTab("prototypes")}
                  className="rounded-xl border border-bronze-faint bg-obsidian/50 p-3 text-left transition-all hover:border-copper/40"
                >
                  <p className="font-title text-sm font-semibold text-ivoire">{p.name}</p>
                  <p className="text-[10px] text-titane/55">{p.phase}</p>
                  <div className="mt-2"><ProgressBar value={p.progress} size="md" /></div>
                  <p className="mt-1 text-[10px] text-titane/55">{p.tests} tests</p>
                </button>
              ))}
            </div>
          </MockCard>
        </motion.div>
      </div>
    </div>
  );
}
