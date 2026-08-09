"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Gamepad2, Sparkles } from "lucide-react";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import type { ConsoleDepartment } from "@/lib/console/types";
import { cn } from "@/lib/utils";
import { MockCard, ProgressBar, StatusBadge } from "../mockup-widgets";
import { poleFadeUp } from "../pole-page-shell";
import { PoleKpiRow, SeeAllLink } from "../pole-kpi-row";
import { PoleFilledPanel, PoleListCard, PoleProtoTabs, PoleStatStrip } from "../pole-proto-tabs";

interface GamingViewProps {
  department: ConsoleDepartment;
}

const TABS = [
  { id: "vue", label: "Vue d'ensemble" },
  { id: "studio", label: "Studio" },
  { id: "builds", label: "Builds" },
  { id: "assets", label: "Assets" },
  { id: "lore", label: "Lore" },
  { id: "wishlist", label: "Wishlist" },
];

const AGENTS = [
  { id: "game_director", name: "Mira Chen", role: "Game Director", load: 88, skills: ["Vision", "Direction", "Godot"] },
  { id: "dev_gaming", name: "Nova Fischer", role: "Game Developer", load: 72, skills: ["Godot", "GDScript", "Gameplay"] },
  { id: "level_designer", name: "Finn Larsen", role: "Level Designer", load: 65, skills: ["Level design", "Narrative", "Godot"] },
  { id: "narrative_designer", name: "Sable Winters", role: "Narrative Designer", load: 55, skills: ["Lore", "Quêtes", "Dialogues"] },
];

const BUILDS = [
  { version: "alpha-0.9.2", project: "Wyrdheim", status: "En test", date: "08 août" },
  { version: "proto-0.4.1", project: "EVE Companion", status: "Stable", date: "05 août" },
  { version: "dev-0.1.0", project: "NAÏA Mini-game", status: "Expérimental", date: "02 août" },
];

const PIPELINE = [
  { label: "Concept", done: true },
  { label: "Prototype", done: true },
  { label: "Vertical Slice", done: true },
  { label: "Alpha", done: true },
  { label: "Beta", done: false },
  { label: "Gold", done: false },
];

type Row = { primary: string; secondary?: string; meta?: string; tone?: "ok" | "warn" | "muted" };
type Panel = { title: string; subtitle: string; stats: { label: string; value: string }[]; cards: { title: string; rows: Row[] }[] };

const PANELS: Record<string, Panel> = {
  studio: {
    title: "Studio Gaming",
    subtitle: "Équipe Wyrdheim · pipeline Alpha",
    stats: [
      { label: "Agents actifs", value: "10" },
      { label: "Charge moy.", value: "70%" },
      { label: "Sprints", value: "3" },
      { label: "Blockers", value: "2" },
    ],
    cards: [
      {
        title: "FOCUS SPRINT",
        rows: [
          { primary: "Level 3 — Forêt des Murmures", secondary: "Finn · level design", meta: "En cours", tone: "warn" },
          { primary: "Combat AI — archers", secondary: "Kenji · comportement", meta: "Review", tone: "ok" },
          { primary: "VFX neige dynamique", secondary: "Diego · particules", meta: "Backlog", tone: "muted" },
        ],
      },
      {
        title: "ÉQUIPE",
        rows: [
          { primary: "Mira Chen", secondary: "Game Director", meta: "88%", tone: "warn" },
          { primary: "Nova Fischer", secondary: "Game Developer", meta: "72%", tone: "ok" },
          { primary: "Sable Winters", secondary: "Narrative", meta: "55%", tone: "ok" },
        ],
      },
    ],
  },
  builds: {
    title: "Builds",
    subtitle: "CI · Godot 4 · export Windows",
    stats: [
      { label: "Builds / mois", value: "19" },
      { label: "Stable", value: "7" },
      { label: "En test", value: "4" },
      { label: "Échoués", value: "2" },
    ],
    cards: [
      {
        title: "DERNIERS BUILDS",
        rows: [
          { primary: "alpha-0.9.2 — Wyrdheim", secondary: "Windows · 08 août", meta: "En test", tone: "warn" },
          { primary: "proto-0.4.1 — EVE Companion", secondary: "WebGL · 05 août", meta: "Stable", tone: "ok" },
          { primary: "dev-0.1.0 — NAÏA Mini-game", secondary: "Prototype · 02 août", meta: "Expérimental", tone: "muted" },
        ],
      },
    ],
  },
  assets: {
    title: "Assets",
    subtitle: "Bibliothèque studio · Godot · FMOD",
    stats: [
      { label: "Total", value: "450" },
      { label: "3D / meshes", value: "128" },
      { label: "Audio", value: "86" },
      { label: "À valider", value: "14" },
    ],
    cards: [
      {
        title: "PIPELINE ASSETS",
        rows: [
          { primary: "Yggdrasil — arbre sacré", secondary: "Priya · environnement", meta: "Validé", tone: "ok" },
          { primary: "SFX murmures forêt", secondary: "Ingrid · sound", meta: "Review", tone: "warn" },
          { primary: "Shader neige procedural", secondary: "Otto · tech art", meta: "WIP", tone: "warn" },
        ],
      },
    ],
  },
  lore: {
    title: "Lore",
    subtitle: "Bible narrative · Wyrdheim",
    stats: [
      { label: "Chapitres", value: "6" },
      { label: "PNJ", value: "24" },
      { label: "Quêtes", value: "18" },
      { label: "Dialogues", value: "112" },
    ],
    cards: [
      {
        title: "ARC NARRATIF",
        rows: [
          { primary: "Chapitre 2 — Murmures de Ygg", secondary: "Sable · draft final", meta: "Actif", tone: "ok" },
          { primary: "Quête — Skald errant", secondary: "Branches A/B", meta: "Draft", tone: "warn" },
          { primary: "Codex — Runes de Midgard", secondary: "Encyclopedia", meta: "Complet", tone: "ok" },
        ],
      },
    ],
  },
  wishlist: {
    title: "Wishlist Steam",
    subtitle: "Wyrdheim · objectif 50 000",
    stats: [
      { label: "Wishlists", value: "12 450" },
      { label: "Objectif", value: "50k" },
      { label: "Progression", value: "25%" },
      { label: "+7 jours", value: "+840" },
    ],
    cards: [
      {
        title: "SOURCES DE TRAFIC",
        rows: [
          { primary: "Trailer Alpha — YouTube", secondary: "Camille · organic", meta: "+420", tone: "ok" },
          { primary: "Steam Next Fest teaser", secondary: "Page store", meta: "+210", tone: "ok" },
          { primary: "Ads Meta — lookalike", secondary: "Léo · CPA élevé", meta: "Pause", tone: "warn" },
        ],
      },
    ],
  },
};

export function MockupGamingView({ department }: GamingViewProps) {
  void department;
  const [tab, setTab] = useState("vue");
  const panel = PANELS[tab];

  return (
    <div className="space-y-3 pb-6">
      <PoleProtoTabs tabs={TABS} active={tab} onChange={setTab} />
      {tab === "vue" || !panel ? (
        <GamingDashboard onNavigateTab={setTab} />
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

function GamingDashboard({ onNavigateTab }: { onNavigateTab: (id: string) => void }) {
  const [selectedId, setSelectedId] = useState(AGENTS[0].id);
  const selected = AGENTS.find((a) => a.id === selectedId) ?? AGENTS[0];

  return (
    <div className="space-y-3">
      <PoleKpiRow
        kpis={[
          { label: "WISHLISTS", value: "12 450", delta: "+840", deltaType: "up", trend: [8, 9, 10, 10.5, 11.5, 12.4], color: "#C08A72", onClick: () => onNavigateTab("wishlist") },
          { label: "BUILDS", value: "19", delta: "+3", deltaType: "up", trend: [12, 14, 15, 16, 18, 19], color: "#22c55e", onClick: () => onNavigateTab("builds") },
          { label: "ASSETS", value: "450", delta: "+28", deltaType: "up", trend: [380, 400, 410, 420, 435, 450], color: "#60a5fa", onClick: () => onNavigateTab("assets") },
          { label: "ALPHA", value: "74%", delta: "+6%", deltaType: "up", trend: [58, 62, 65, 68, 71, 74], color: "#C08A72", onClick: () => onNavigateTab("studio") },
        ]}
      />

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-12">
        <motion.div className="lg:col-span-8" custom={4} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="WYRDHEIM — PIPELINE STUDIO" action={<SeeAllLink onClick={() => onNavigateTab("studio")} label="Studio" />}>
            <div className="mb-3 flex items-center justify-between rounded-lg border border-copper/30 bg-copper/10 px-3 py-2">
              <div>
                <p className="font-title text-sm font-semibold text-ivoire">Wyrdheim</p>
                <p className="text-[10px] text-titane/55">Alpha · Godot 4 · Dark fantasy nordique</p>
              </div>
              <StatusBadge status="active">Alpha 74%</StatusBadge>
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
            <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2">
              <div className="rounded-xl border border-bronze-faint bg-obsidian/50 p-3">
                <p className="text-[10px] uppercase tracking-wider text-titane/50">Focus — {selected.name}</p>
                <p className="mt-1 text-[12px] text-ivoire/90">Level 3 — Forêt des Murmures</p>
                <div className="mt-2 flex flex-wrap gap-1">
                  {selected.skills.map((s) => (
                    <span key={s} className="rounded-full bg-obsidian-2 px-1.5 py-0.5 text-[9px] text-titane/70">{s}</span>
                  ))}
                </div>
              </div>
              <div className="rounded-xl border border-bronze-faint bg-obsidian/50 p-3">
                <p className="text-[10px] uppercase tracking-wider text-titane/50">Lore actif</p>
                <p className="mt-1 text-[12px] text-ivoire/90">Chapitre 2 — Les Murmures de Ygg</p>
                <button type="button" onClick={() => onNavigateTab("lore")} className="mt-2 text-[10px] text-copper hover:underline">
                  Ouvrir le lore →
                </button>
              </div>
            </div>
          </MockCard>
        </motion.div>

        <motion.div className="lg:col-span-4 space-y-3" custom={5} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="PIPELINE" action={<Gamepad2 className="h-3.5 w-3.5 text-copper/70" />}>
            <div className="space-y-2">
              {PIPELINE.map((step) => (
                <div key={step.label} className="flex items-center gap-2">
                  <div className={cn("h-2 w-2 rounded-full", step.done ? "bg-copper" : "bg-obsidian-2")} />
                  <span className={step.done ? "text-[11px] text-ivoire/80" : "text-[11px] text-titane/40"}>{step.label}</span>
                </div>
              ))}
            </div>
          </MockCard>
          <MockCard title="STEAM WISHLIST" action={<Sparkles className="h-3.5 w-3.5 text-copper/70" />}>
            <div className="text-center">
              <p className="font-title text-2xl font-semibold text-ivoire">12 450</p>
              <p className="text-[9px] uppercase tracking-wider text-titane/50">wishlists Wyrdheim</p>
              <div className="mt-2"><ProgressBar value={25} size="md" /></div>
              <p className="mt-1 text-[10px] text-titane/50">Objectif 2026 : 50 000 (25%)</p>
            </div>
          </MockCard>
        </motion.div>
      </div>

      <motion.div custom={6} variants={poleFadeUp} initial="hidden" animate="show">
        <MockCard title="BUILDS RÉCENTS" action={<SeeAllLink onClick={() => onNavigateTab("builds")} label="Tous les builds" />}>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
            {BUILDS.map((b) => (
              <button
                key={b.version}
                type="button"
                onClick={() => onNavigateTab("builds")}
                className="rounded-xl border border-bronze-faint bg-obsidian/50 p-3 text-left transition-all hover:border-copper/40"
              >
                <p className="font-title text-sm font-semibold text-copper">{b.version}</p>
                <p className="text-[10px] text-titane/55">{b.project}</p>
                <div className="mt-2 flex items-center justify-between">
                  <StatusBadge status={b.status === "Stable" ? "success" : "active"}>{b.status}</StatusBadge>
                  <span className="text-[9px] text-titane/45">{b.date}</span>
                </div>
              </button>
            ))}
          </div>
        </MockCard>
      </motion.div>
    </div>
  );
}
