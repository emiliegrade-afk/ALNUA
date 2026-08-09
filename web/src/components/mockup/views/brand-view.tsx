"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Image as ImageIcon, Pen, Type } from "lucide-react";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import type { ConsoleDepartment } from "@/lib/console/types";
import { cn } from "@/lib/utils";
import { MockCard, ProgressBar, StatusBadge } from "../mockup-widgets";
import { poleFadeUp } from "../pole-page-shell";
import { PoleKpiRow, SeeAllLink } from "../pole-kpi-row";
import {
  PoleFilledPanel,
  PoleListCard,
  PoleProtoTabs,
  PoleStatStrip,
} from "../pole-proto-tabs";

interface BrandViewProps {
  department: ConsoleDepartment;
}

const TABS = [
  { id: "dashboard", label: "Dashboard" },
  { id: "kits", label: "Kits" },
  { id: "palette", label: "Palette" },
  { id: "assets", label: "Assets" },
  { id: "guidelines", label: "Guidelines" },
];

type ListRow = { primary: string; secondary?: string; meta?: string; tone?: "ok" | "warn" | "muted" };
type PanelDef = {
  title: string;
  subtitle: string;
  stats: { label: string; value: string }[];
  left: { title: string; rows: ListRow[] };
  right: { title: string; rows: ListRow[] };
};

const PALETTE = [
  { name: "Obsidienne", hex: "#0E1014", role: "background" },
  { name: "Ivoire", hex: "#F5F2EA", role: "text" },
  { name: "Titane", hex: "#A7ADB5", role: "secondary" },
  { name: "Cuivre Rosé", hex: "#C08A72", role: "accent" },
];

const KITS = [
  { name: "ALNUA Hub", status: "Publié", usage: 92 },
  { name: "NAÏA", status: "En cours", usage: 68 },
  { name: "NUAWAY", status: "Brouillon", usage: 34 },
  { name: "RESONANCE", status: "Brouillon", usage: 22 },
];

const ASSETS = [
  { name: "Logo principal", type: "SVG" },
  { name: "Star mark", type: "SVG" },
  { name: "Avatar Instagram", type: "PNG" },
  { name: "Favicon 32", type: "ICO" },
];

const TYPOGRAPHY = [
  { name: "Space Grotesk", usage: "Titres" },
  { name: "Avenir Next", usage: "Sous-titres" },
  { name: "Inter", usage: "Corps" },
];

const CHECKLIST = [
  { label: "Palette validée", done: true },
  { label: "Logo vectorisé", done: true },
  { label: "Typography lockée", done: true },
  { label: "Composants Tailwind", done: true },
  { label: "Guidelines web", done: false },
  { label: "Kits produits", done: false },
];

const SECONDARY: Record<string, PanelDef> = {
  kits: {
    title: "Kits",
    subtitle: "Brand kits par produit ALNUA",
    stats: [
      { label: "Publiés", value: "1" },
      { label: "En cours", value: "1" },
      { label: "Brouillons", value: "2" },
      { label: "Couverture", value: "67%" },
      { label: "Assets liés", value: "28" },
    ],
    left: {
      title: "KITS PRODUITS",
      rows: [
        { primary: "ALNUA Hub", secondary: "Charte complète · usage 92%", meta: "Publié", tone: "ok" },
        { primary: "NAÏA", secondary: "Palette + logo · usage 68%", meta: "En cours", tone: "warn" },
        { primary: "NUAWAY", secondary: "Moodboard initial · usage 34%", meta: "Brouillon", tone: "muted" },
        { primary: "RESONANCE", secondary: "Direction artistique · usage 22%", meta: "Brouillon", tone: "muted" },
      ],
    },
    right: {
      title: "PROCHAINES ÉTAPES",
      rows: [
        { primary: "Valider kit NAÏA", secondary: "Revue Iris + Camille", meta: "Cette sem.", tone: "warn" },
        { primary: "Exporter tokens NUAWAY", secondary: "Tailwind + Figma", meta: "Août", tone: "muted" },
        { primary: "Packaging RESONANCE", secondary: "Couverture + avatar", meta: "Q3", tone: "muted" },
      ],
    },
  },
  palette: {
    title: "Palette",
    subtitle: "Couleurs officielles et rôles d'usage",
    stats: [
      { label: "Couleurs", value: "4" },
      { label: "Accents", value: "1" },
      { label: "Contraste AA", value: "OK" },
      { label: "Tokens CSS", value: "12" },
      { label: "Validée", value: "Oui" },
    ],
    left: {
      title: "COULEURS PRINCIPALES",
      rows: [
        { primary: "Obsidienne #0E1014", secondary: "Background · surfaces", meta: "bg", tone: "muted" },
        { primary: "Ivoire #F5F2EA", secondary: "Texte principal", meta: "text", tone: "ok" },
        { primary: "Titane #A7ADB5", secondary: "Secondaire · labels", meta: "muted", tone: "muted" },
        { primary: "Cuivre Rosé #C08A72", secondary: "Accent · CTAs", meta: "accent", tone: "ok" },
      ],
    },
    right: {
      title: "USAGE UI",
      rows: [
        { primary: "Boutons primaires", secondary: "Fond cuivre · texte ivoire", meta: "OK", tone: "ok" },
        { primary: "Bordures", secondary: "bronze-faint sur obsidienne", meta: "OK", tone: "ok" },
        { primary: "États erreur", secondary: "À aligner sur charte", meta: "Todo", tone: "warn" },
      ],
    },
  },
  assets: {
    title: "Assets",
    subtitle: "Fichiers brand prêts à exporter",
    stats: [
      { label: "Fichiers", value: "24" },
      { label: "SVG", value: "11" },
      { label: "PNG", value: "9" },
      { label: "ICO", value: "2" },
      { label: "À générer", value: "4" },
    ],
    left: {
      title: "ASSETS RÉCENTS",
      rows: [
        { primary: "Logo principal", secondary: "SVG · monochrome + couleur", meta: "Prêt", tone: "ok" },
        { primary: "Star mark", secondary: "SVG · icône app", meta: "Prêt", tone: "ok" },
        { primary: "Avatar Instagram", secondary: "PNG 1080²", meta: "Prêt", tone: "ok" },
        { primary: "Favicon 32", secondary: "ICO · Hub web", meta: "Prêt", tone: "ok" },
      ],
    },
    right: {
      title: "FILE D'ATTENTE",
      rows: [
        { primary: "Open Graph Hub", secondary: "1200×630 PNG", meta: "À faire", tone: "warn" },
        { primary: "Banner LinkedIn", secondary: "1584×396", meta: "À faire", tone: "warn" },
        { primary: "Pack stickers Stories", secondary: "9 frames PNG", meta: "Q3", tone: "muted" },
      ],
    },
  },
  guidelines: {
    title: "Guidelines",
    subtitle: "Checklist charte et règles d'usage",
    stats: [
      { label: "Complétion", value: "67%" },
      { label: "Validés", value: "4/6" },
      { label: "Docs", value: "3" },
      { label: "Blocages", value: "2" },
      { label: "Revues", value: "1" },
    ],
    left: {
      title: "CHECKLIST CHARTE",
      rows: [
        { primary: "Palette validée", secondary: "Obsidienne · Ivoire · Cuivre", meta: "Fait", tone: "ok" },
        { primary: "Logo vectorisé", secondary: "SVG principal + mark", meta: "Fait", tone: "ok" },
        { primary: "Typography lockée", secondary: "Space Grotesk · Avenir · Inter", meta: "Fait", tone: "ok" },
        { primary: "Composants Tailwind", secondary: "Tokens brand dans globals", meta: "Fait", tone: "ok" },
        { primary: "Guidelines web", secondary: "Règles spacing & CTA", meta: "Ouvert", tone: "warn" },
        { primary: "Kits produits", secondary: "NAÏA / NUAWAY / RESONANCE", meta: "Ouvert", tone: "warn" },
      ],
    },
    right: {
      title: "RÈGLES CLÉS",
      rows: [
        { primary: "Jamais de violet générique", secondary: "Accent = cuivre uniquement", meta: "Strict", tone: "ok" },
        { primary: "Logo sur fond sombre", secondary: "Ivoire ou cuivre", meta: "Strict", tone: "ok" },
        { primary: "Pas de glow excessif", secondary: "UI Hub sobre", meta: "Conseil", tone: "muted" },
      ],
    },
  },
};

export function MockupBrandView({ department }: BrandViewProps) {
  const [tab, setTab] = useState("dashboard");
  const panel = SECONDARY[tab];

  return (
    <div className="pb-8">
      <PoleProtoTabs tabs={TABS} active={tab} onChange={setTab} />
      {tab === "dashboard" ? (
        <BrandDashboard department={department} onNavigateTab={setTab} />
      ) : panel ? (
        <PoleFilledPanel title={panel.title} subtitle={panel.subtitle} onBack={() => setTab("dashboard")}>
          <PoleStatStrip items={panel.stats} />
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
            <PoleListCard title={panel.left.title} rows={panel.left.rows} />
            <PoleListCard title={panel.right.title} rows={panel.right.rows} />
          </div>
        </PoleFilledPanel>
      ) : null}
    </div>
  );
}

function BrandDashboard({
  department,
  onNavigateTab,
}: {
  department: ConsoleDepartment;
  onNavigateTab: (id: string) => void;
}) {
  return (
    <div className="space-y-3">
      <PoleKpiRow
        kpis={[
          { label: "KITS PUBLIÉS", value: "1", delta: "stable", deltaType: "neutral", trend: [1, 1, 1, 1, 1, 1], color: "#22c55e", onClick: () => onNavigateTab("kits") },
          { label: "EN COURS", value: "3", delta: "+1", deltaType: "up", trend: [1, 2, 2, 2, 3, 3], color: "#C08A72", onClick: () => onNavigateTab("kits") },
          { label: "ASSETS", value: "4", delta: "+2", deltaType: "up", trend: [1, 2, 2, 3, 3, 4], color: "#60a5fa", onClick: () => onNavigateTab("assets") },
          { label: "CHECKLIST", value: "67%", delta: "+8%", deltaType: "up", trend: [50, 55, 58, 60, 63, 67], color: "#C08A72", onClick: () => onNavigateTab("guidelines") },
        ]}
      />

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-12">
        <motion.div className="lg:col-span-6" custom={4} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="PALETTE ALNUA" action={<SeeAllLink onClick={() => onNavigateTab("palette")} label="Palette" />}>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {PALETTE.map((c) => (
                <button key={c.name} type="button" onClick={() => onNavigateTab("palette")} className="overflow-hidden rounded-xl border border-bronze-faint text-left transition-all hover:border-copper/40">
                  <div className="h-16 w-full" style={{ background: c.hex }} />
                  <div className="bg-obsidian/50 p-2">
                    <p className="text-[10px] font-medium text-ivoire/90">{c.name}</p>
                    <p className="text-[8px] text-titane/50">{c.hex}</p>
                  </div>
                </button>
              ))}
            </div>
          </MockCard>
        </motion.div>

        <motion.div className="lg:col-span-6" custom={5} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="BRAND KITS" action={<ImageIcon className="h-3.5 w-3.5 text-copper/70" />}>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {KITS.map((k) => (
                <button key={k.name} type="button" onClick={() => onNavigateTab("kits")} className="rounded-xl border border-bronze-faint bg-obsidian/50 p-3 text-left transition-all hover:border-copper/40">
                  <div className="flex items-center justify-between">
                    <p className="text-[11px] font-medium text-ivoire/90">{k.name}</p>
                    <StatusBadge status={k.status === "Publié" ? "success" : k.status === "En cours" ? "active" : "warning"}>{k.status}</StatusBadge>
                  </div>
                  <div className="mt-2"><ProgressBar value={k.usage} /></div>
                  <p className="mt-1 text-[9px] text-titane/50">Usage {k.usage}%</p>
                </button>
              ))}
            </div>
          </MockCard>
        </motion.div>
      </div>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-12">
        <motion.div className="lg:col-span-3" custom={6} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="TYPOGRAPHY" action={<Type className="h-3.5 w-3.5 text-copper/70" />}>
            <div className="space-y-2">
              {TYPOGRAPHY.map((t) => (
                <div key={t.name} className="rounded-lg border border-bronze-faint bg-obsidian/50 px-3 py-2">
                  <p className="text-[11px] font-medium text-ivoire/90" style={{ fontFamily: t.name === "Space Grotesk" ? "var(--font-space-grotesk)" : undefined }}>{t.name}</p>
                  <p className="text-[9px] text-titane/55">{t.usage}</p>
                </div>
              ))}
            </div>
          </MockCard>
        </motion.div>

        <motion.div className="lg:col-span-5" custom={7} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="ASSETS RÉCENTS" action={<SeeAllLink onClick={() => onNavigateTab("assets")} label="Assets" />}>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {ASSETS.map((a) => (
                <button key={a.name} type="button" onClick={() => onNavigateTab("assets")} className={cn("flex flex-col items-center justify-center rounded-xl border border-bronze-faint bg-obsidian/50 p-3 text-center transition-all hover:border-copper/40")}>
                  <div className="mb-2 h-10 w-10 rounded-lg bg-obsidian-2" />
                  <p className="text-[10px] font-medium text-ivoire/90">{a.name}</p>
                  <p className="text-[8px] text-titane/50">{a.type}</p>
                </button>
              ))}
            </div>
          </MockCard>
        </motion.div>

        <motion.div className="lg:col-span-4 space-y-3" custom={8} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="CHECKLIST CHARTE" action={<Pen className="h-3.5 w-3.5 text-copper/70" />}>
            <div className="space-y-1.5">
              {CHECKLIST.map((t) => (
                <button key={t.label} type="button" onClick={() => onNavigateTab("guidelines")} className="flex w-full items-center gap-2 rounded-lg border border-bronze-faint bg-obsidian/50 px-3 py-1.5 text-left hover:border-copper/40">
                  <div className={`h-3 w-3 rounded-full border ${t.done ? "border-online bg-online" : "border-titane/40"}`} />
                  <span className={t.done ? "text-[10px] text-titane/50 line-through" : "text-[10px] text-ivoire/80"}>{t.label}</span>
                </button>
              ))}
            </div>
          </MockCard>
          <MockCard title="ÉQUIPE BRAND">
            <div className="space-y-2">
              {department.agents.map((a) => (
                <div key={a.id} className="flex items-center gap-2">
                  <AgentAvatar agentId={a.id} name={a.name} size={32} />
                  <div className="min-w-0 flex-1">
                    <p className="text-[11px] font-medium text-ivoire/90">{a.name}</p>
                    <p className="text-[9px] text-titane/55">{a.role}</p>
                  </div>
                </div>
              ))}
            </div>
          </MockCard>
        </motion.div>
      </div>
    </div>
  );
}
