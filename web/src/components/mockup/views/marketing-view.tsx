"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Calendar, TrendingUp, Users } from "lucide-react";
import type { ConsoleDepartment } from "@/lib/console/types";
import { MockCard, StatusBadge } from "../mockup-widgets";
import { poleFadeUp } from "../pole-page-shell";
import { PoleKpiRow, SeeAllLink } from "../pole-kpi-row";
import {
  PoleFilledPanel,
  PoleListCard,
  PoleProtoTabs,
  PoleStatStrip,
  type PoleTab,
} from "../pole-proto-tabs";
import { MARKETING_SECONDARY } from "./marketing-secondary";

interface MarketingViewProps {
  department: ConsoleDepartment;
}

const TABS: PoleTab[] = [
  { id: "vue", label: "Vue globale" },
  { id: "campagnes", label: "Campagnes" },
  { id: "content", label: "Content Studio" },
  { id: "social", label: "Social Media" },
  { id: "seo", label: "SEO" },
  { id: "ads", label: "Ads" },
  { id: "analytics", label: "Analytics" },
  { id: "auto", label: "Automatisation" },
  { id: "brand", label: "Brand Center" },
];

const CAMPAIGNS = [
  { name: "Lancement NAÏA", platform: "Instagram", roi: "4.2x", budget: "2.4k€", status: "Active" },
  { name: "NUAWAY Summer", platform: "TikTok", roi: "3.8x", budget: "1.8k€", status: "Active" },
  { name: "Brand ALNUA", platform: "LinkedIn", roi: "2.9x", budget: "3.2k€", status: "Active" },
  { name: "EVE Demo", platform: "YouTube", roi: "3.1x", budget: "1.2k€", status: "Active" },
];

const CHANNELS = [
  { name: "Instagram", reach: "540K", engagement: "8.2%", conversion: "3.1%", roi: "4.1x" },
  { name: "TikTok", reach: "420K", engagement: "12.4%", conversion: "2.8%", roi: "3.8x" },
  { name: "YouTube", reach: "210K", engagement: "6.1%", conversion: "2.2%", roi: "3.2x" },
  { name: "LinkedIn", reach: "180K", engagement: "5.6%", conversion: "4.5%", roi: "2.9x" },
  { name: "Email", reach: "95K", engagement: "24%", conversion: "6.2%", roi: "5.2x" },
];

const FUNNEL = [
  { label: "Visiteurs", value: "152 480", pct: "100%", width: 100 },
  { label: "Intéressés", value: "28 450", pct: "18.7%", width: 68 },
  { label: "Engagés", value: "9 622", pct: "6.3%", width: 48 },
  { label: "Abonnés", value: "2 941", pct: "1.9%", width: 32 },
  { label: "Clients", value: "712", pct: "0.5%", width: 18 },
];

const TOP_CONTENT = [
  { title: "Behind the scenes NAÏA", platform: "Reel Instagram", reach: "128K", eng: "8.4%" },
  { title: "EVE demo reel", platform: "YouTube", reach: "96K", eng: "7.1%" },
  { title: "NOMAD journey", platform: "TikTok", reach: "84K", eng: "11.2%" },
  { title: "ALNUA manifesto", platform: "LinkedIn", reach: "58K", eng: "5.8%" },
];

const CALENDAR = [
  { time: "08:00", title: "Instagram Post", status: "Publié" },
  { time: "09:15", title: "Newsletter", status: "Envoyée" },
  { time: "11:00", title: "YouTube", status: "Programmé" },
  { time: "14:00", title: "TikTok", status: "En cours" },
  { time: "17:00", title: "LinkedIn", status: "Programmé" },
  { time: "20:00", title: "Threads", status: "Programmé" },
];

const SECONDARY: Record<string, PanelDef> = {
  campagnes: {
    title: "Campagnes",
    subtitle: "Campagnes actives et performance ROI",
    stats: [
      { label: "Actives", value: "4" },
      { label: "Budget", value: "8.6k€" },
      { label: "ROI moy.", value: "3.5x" },
      { label: "Leads", value: "712" },
      { label: "CA", value: "18.2k€" },
    ],
    left: {
      title: "CAMPAGNES ACTIVES",
      rows: [
        { primary: "Lancement NAÏA", secondary: "Instagram · 2.4k€", meta: "4.2x", tone: "ok" },
        { primary: "NUAWAY Summer", secondary: "TikTok · 1.8k€", meta: "3.8x", tone: "ok" },
        { primary: "Brand ALNUA", secondary: "LinkedIn · 3.2k€", meta: "2.9x", tone: "ok" },
        { primary: "EVE Demo", secondary: "YouTube · 1.2k€", meta: "3.1x", tone: "ok" },
      ],
    },
    right: {
      title: "À LANCER",
      rows: [
        { primary: "RESONANCE soft launch", secondary: "Meta Ads · brief prêt", meta: "Q3", tone: "warn" },
        { primary: "Retargeting Hub", secondary: "Google · audiences chaudes", meta: "Août", tone: "muted" },
        { primary: "Newsletter back-to-school", secondary: "Email · freelances", meta: "Sept.", tone: "muted" },
      ],
    },
  },
  content: {
    title: "Content Studio",
    subtitle: "Pipeline éditorial multi-pôles",
    stats: [
      { label: "En file", value: "18" },
      { label: "Publiés 7j", value: "24" },
      { label: "Drafts", value: "9" },
      { label: "Validés", value: "6" },
      { label: "Reach top", value: "128K" },
    ],
    left: {
      title: "TOP CONTENUS",
      rows: [
        { primary: "Behind the scenes NAÏA", secondary: "Reel Instagram", meta: "128K", tone: "ok" },
        { primary: "EVE demo reel", secondary: "YouTube", meta: "96K", tone: "ok" },
        { primary: "NOMAD journey", secondary: "TikTok", meta: "84K", tone: "ok" },
        { primary: "ALNUA manifesto", secondary: "LinkedIn", meta: "58K", tone: "muted" },
      ],
    },
    right: {
      title: "EN PRODUCTION",
      rows: [
        { primary: "Carrousel skills Hub", secondary: "Sofia · Instagram", meta: "Draft", tone: "warn" },
        { primary: "Thread R&D incubateur", secondary: "Anouk · LinkedIn", meta: "Revue", tone: "warn" },
        { primary: "Short Gaming Studio", secondary: "Kael · TikTok", meta: "Tournage", tone: "muted" },
      ],
    },
  },
  social: {
    title: "Social Media",
    subtitle: "Présence organique et calendrier",
    stats: [
      { label: "Followers", value: "86.4K" },
      { label: "+7j", value: "+2.1K" },
      { label: "Eng. moy.", value: "7.8%" },
      { label: "Posts/sem.", value: "14" },
      { label: "Stories", value: "22" },
    ],
    left: {
      title: "CANAUX",
      rows: [
        { primary: "Instagram", secondary: "540K reach · eng. 8.2%", meta: "Lead", tone: "ok" },
        { primary: "TikTok", secondary: "420K reach · eng. 12.4%", meta: "Croissance", tone: "ok" },
        { primary: "LinkedIn", secondary: "180K reach · eng. 5.6%", meta: "B2B", tone: "muted" },
        { primary: "YouTube", secondary: "210K reach · eng. 6.1%", meta: "Stable", tone: "muted" },
      ],
    },
    right: {
      title: "AUJOURD'HUI",
      rows: [
        { primary: "08:00 Instagram Post", secondary: "Publié", meta: "OK", tone: "ok" },
        { primary: "14:00 TikTok", secondary: "En cours", meta: "Live", tone: "warn" },
        { primary: "17:00 LinkedIn", secondary: "Programmé", meta: "Queue", tone: "muted" },
        { primary: "20:00 Threads", secondary: "Programmé", meta: "Queue", tone: "muted" },
      ],
    },
  },
  seo: {
    title: "SEO",
    subtitle: "Visibilité organique et contenu evergreen",
    stats: [
      { label: "Mots-clés", value: "142" },
      { label: "Top 10", value: "28" },
      { label: "Trafic org.", value: "18.4K" },
      { label: "Pages", value: "36" },
      { label: "Score tech", value: "91" },
    ],
    left: {
      title: "PAGES PERFORMANTES",
      rows: [
        { primary: "/blog/agents-llm-ops", secondary: "Position 4 · +1.2K visites", meta: "↑", tone: "ok" },
        { primary: "/produits/naia", secondary: "Position 7 · intent commercial", meta: "↑", tone: "ok" },
        { primary: "/hub/docs", secondary: "Position 11 · longue traîne", meta: "→", tone: "muted" },
      ],
    },
    right: {
      title: "OPPORTUNITÉS",
      rows: [
        { primary: "Cluster agent orchestration", secondary: "Gaps vs concurrent", meta: "Priorité", tone: "warn" },
        { primary: "FAQ NAÏA wellness", secondary: "Featured snippets cibles", meta: "Août", tone: "muted" },
        { primary: "Internal linking Hub", secondary: "12 orphelines détectées", meta: "Quick win", tone: "ok" },
      ],
    },
  },
  ads: {
    title: "Ads",
    subtitle: "Publicité payante Meta · Google · TikTok",
    stats: [
      { label: "Spend 30j", value: "6.8k€" },
      { label: "ROAS", value: "3.4x" },
      { label: "CPA", value: "24€" },
      { label: "CTR", value: "2.9%" },
      { label: "Conv.", value: "284" },
    ],
    left: {
      title: "COMPTES ACTIFS",
      rows: [
        { primary: "Meta Ads — NAÏA", secondary: "Prospecting + retarget", meta: "2.1k€", tone: "ok" },
        { primary: "Google Search — Hub", secondary: "Brand + génériques", meta: "1.9k€", tone: "ok" },
        { primary: "TikTok — NUAWAY", secondary: "Spark Ads créateurs", meta: "1.6k€", tone: "ok" },
        { primary: "LinkedIn — ALNUA", secondary: "Thought leadership", meta: "1.2k€", tone: "muted" },
      ],
    },
    right: {
      title: "ALERTES LÉO",
      rows: [
        { primary: "Fréquence Meta > 3.2", secondary: "Créas à renouveler", meta: "Attention", tone: "warn" },
        { primary: "CPA Google en baisse", secondary: "−18% vs semaine préc.", meta: "OK", tone: "ok" },
        { primary: "Budget TikTok 82%", secondary: "Recharge avant vendredi", meta: "Watch", tone: "warn" },
      ],
    },
  },
  analytics: {
    title: "Analytics",
    subtitle: "Mesure multi-canal et attribution",
    stats: [
      { label: "Reach", value: "1.24M" },
      { label: "Conv.", value: "4.8%" },
      { label: "CA", value: "18.2k€" },
      { label: "ROI", value: "287%" },
      { label: "Sessions", value: "152K" },
    ],
    left: {
      title: "FUNNEL",
      rows: [
        { primary: "Visiteurs", secondary: "152 480", meta: "100%", tone: "muted" },
        { primary: "Intéressés", secondary: "28 450", meta: "18.7%", tone: "ok" },
        { primary: "Engagés", secondary: "9 622", meta: "6.3%", tone: "ok" },
        { primary: "Clients", secondary: "712", meta: "0.5%", tone: "ok" },
      ],
    },
    right: {
      title: "ATTRIBUTION",
      rows: [
        { primary: "Instagram → essai NAÏA", secondary: "Last-click dominant", meta: "38%", tone: "ok" },
        { primary: "SEO → Hub demo", secondary: "Assisted conversions", meta: "22%", tone: "ok" },
        { primary: "Email → upgrade", secondary: "Nurture Série B", meta: "17%", tone: "muted" },
      ],
    },
  },
  auto: {
    title: "Automatisation",
    subtitle: "Workflows n8n et publications planifiées",
    stats: [
      { label: "Flows actifs", value: "11" },
      { label: "Runs 24h", value: "86" },
      { label: "Échecs", value: "2" },
      { label: "Slots", value: "48" },
      { label: "Uptime", value: "99.1%" },
    ],
    left: {
      title: "WORKFLOWS",
      rows: [
        { primary: "Publish social queue", secondary: "n8n · IG/TikTok/LI", meta: "OK", tone: "ok" },
        { primary: "Brief → Sofia draft", secondary: "Webhook Hub → Content", meta: "OK", tone: "ok" },
        { primary: "Ads spend alert", secondary: "Budget > 85% → Léo", meta: "OK", tone: "ok" },
        { primary: "Weekly digest Camille", secondary: "Lundi 08:00", meta: "2 fails", tone: "warn" },
      ],
    },
    right: {
      title: "FILE PROGRAMMÉE",
      rows: [
        { primary: "Carrousel NAÏA · IG", secondary: "Demain 09:00", meta: "Queued", tone: "muted" },
        { primary: "Reel EVE · TikTok", secondary: "Demain 18:30", meta: "Queued", tone: "muted" },
        { primary: "Newsletter Hub", secondary: "Mercredi 10:00", meta: "Draft", tone: "warn" },
      ],
    },
  },
  brand: {
    title: "Brand Center",
    subtitle: "Alignement marque et assets marketing",
    stats: [
      { label: "Kits liés", value: "4" },
      { label: "Assets MKT", value: "36" },
      { label: "Templates", value: "12" },
      { label: "Compliance", value: "94%" },
      { label: "Revues", value: "3" },
    ],
    left: {
      title: "ASSETS CAMPAGNES",
      rows: [
        { primary: "Pack NAÏA Stories", secondary: "9 frames · charte validée", meta: "OK", tone: "ok" },
        { primary: "Thumbnails YouTube EVE", secondary: "Cuivre + ivoire", meta: "OK", tone: "ok" },
        { primary: "Bannières LinkedIn ALNUA", secondary: "3 variantes", meta: "Revue", tone: "warn" },
      ],
    },
    right: {
      title: "GARDES-FOUS",
      rows: [
        { primary: "Pas de violet générique", secondary: "Accent = cuivre uniquement", meta: "Strict", tone: "ok" },
        { primary: "Logo sur fond sombre", secondary: "Ivoire ou cuivre", meta: "Strict", tone: "ok" },
        { primary: "Claims santé NAÏA", secondary: "Validation legal avant pub", meta: "Watch", tone: "warn" },
      ],
    },
  },
};

export function MockupMarketingView({ department }: MarketingViewProps) {
  void department;
  const [tab, setTab] = useState("vue");
  const panel = SECONDARY[tab];

  return (
    <div className="pb-8">
      <PoleProtoTabs tabs={TABS} active={tab} onChange={setTab} />
      {tab === "vue" ? (
        <MarketingDashboard onNavigateTab={setTab} />
      ) : panel ? (
        <PoleFilledPanel title={panel.title} subtitle={panel.subtitle} onBack={() => setTab("vue")}>
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

function MarketingDashboard({ onNavigateTab }: { onNavigateTab: (id: string) => void }) {
  const kpis = [
    { label: "REACH TOTAL", value: "1.24M", delta: "+18.6%", deltaType: "up" as const, trend: [40, 45, 52, 48, 60, 68], color: "#22c55e", onClick: () => onNavigateTab("analytics") },
    { label: "NOUVEAUX FOLLOWERS", value: "+2 140", delta: "+24.5%", deltaType: "up" as const, trend: [20, 28, 35, 42, 50, 58], color: "#22c55e", onClick: () => onNavigateTab("social") },
    { label: "TAUX DE CONVERSION", value: "4.8%", delta: "+0.9%", deltaType: "up" as const, trend: [3.2, 3.5, 3.8, 4.1, 4.4, 4.8], color: "#22c55e", onClick: () => onNavigateTab("analytics") },
    { label: "CA GÉNÉRÉ", value: "18 250 €", delta: "+32.4%", deltaType: "up" as const, trend: [12, 13, 14, 15, 16, 18], color: "#C08A72", onClick: () => onNavigateTab("ads") },
    { label: "ROI GLOBAL", value: "287%", delta: "+42.1%", deltaType: "up" as const, trend: [180, 200, 220, 240, 260, 287], color: "#22c55e", onClick: () => onNavigateTab("campagnes") },
  ];

  return (
    <div className="space-y-3">
      <PoleKpiRow kpis={kpis} />
      <div className="grid grid-cols-1 gap-3 xl:grid-cols-12">
        <motion.div className="xl:col-span-9" custom={5} variants={poleFadeUp} initial="hidden" animate="show">
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-2 2xl:grid-cols-4">
            <MockCard title="CAMPAGNES ACTIVES" action={<SeeAllLink onClick={() => onNavigateTab("campagnes")} label="Voir toutes" />}>
              <div className="space-y-2.5">
                {CAMPAIGNS.map((c) => (
                  <button key={c.name} type="button" onClick={() => onNavigateTab("campagnes")} className="flex w-full items-center justify-between rounded-lg border border-bronze-faint bg-obsidian/50 px-3 py-2 text-left transition-all hover:border-copper/40">
                    <div>
                      <p className="text-[12px] font-medium text-ivoire/90">{c.name}</p>
                      <p className="text-[10px] text-titane/50">{c.platform} · {c.budget}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-title text-sm font-semibold text-copper">{c.roi}</p>
                      <StatusBadge status="active">{c.status}</StatusBadge>
                    </div>
                  </button>
                ))}
              </div>
            </MockCard>

            <MockCard title="PERFORMANCES PAR CANAL" action={<TrendingUp className="h-3.5 w-3.5 text-copper/70" />}>
              <div className="mb-2 grid grid-cols-5 gap-1 text-[8px] uppercase tracking-wider text-titane/40">
                <span>Canal</span><span>Reach</span><span>Eng.</span><span>Conv.</span><span>ROI</span>
              </div>
              <div className="space-y-2">
                {CHANNELS.map((c) => (
                  <div key={c.name} className="grid grid-cols-5 gap-1 text-[10px]">
                    <span className="truncate text-ivoire/85">{c.name}</span>
                    <span className="text-titane/60">{c.reach}</span>
                    <span className="text-titane/60">{c.engagement}</span>
                    <span className="text-titane/60">{c.conversion}</span>
                    <span className="font-medium text-copper">{c.roi}</span>
                  </div>
                ))}
              </div>
            </MockCard>

            <MockCard title="ENTONNOIR DE CONVERSION" action={<Users className="h-3.5 w-3.5 text-copper/70" />}>
              <div className="space-y-2">
                {FUNNEL.map((step) => (
                  <div key={step.label} className="flex items-center gap-2">
                    <div className="flex items-center justify-center rounded-md bg-gradient-to-r from-copper/40 to-copper/15 py-1.5 transition-all" style={{ width: `${step.width}%`, minWidth: 56 }}>
                      <span className="text-[9px] font-medium text-copper">{step.label}</span>
                    </div>
                    <div className="ml-auto text-right">
                      <p className="text-[11px] text-ivoire/85">{step.value}</p>
                      <p className="text-[9px] text-titane/45">{step.pct}</p>
                    </div>
                  </div>
                ))}
              </div>
            </MockCard>

            <MockCard title="TOP CONTENUS" action={<SeeAllLink onClick={() => onNavigateTab("content")} label="Voir tout" />}>
              <div className="space-y-2.5">
                {TOP_CONTENT.map((c, i) => (
                  <button key={c.title} type="button" onClick={() => onNavigateTab("content")} className="flex w-full items-center gap-3 rounded-lg border border-bronze-faint bg-obsidian/50 p-2 text-left transition-all hover:border-copper/40">
                    <div className="flex h-9 w-9 items-center justify-center rounded-md bg-obsidian-2 font-title text-sm text-copper">{i + 1}</div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[11px] font-medium text-ivoire/90">{c.title}</p>
                      <p className="text-[10px] text-titane/50">{c.platform} · {c.reach} · {c.eng}</p>
                    </div>
                  </button>
                ))}
              </div>
            </MockCard>
          </div>
        </motion.div>

        <motion.div className="xl:col-span-3" custom={8} variants={poleFadeUp} initial="hidden" animate="show">
          <MockCard title="CALENDRIER AUJOURD'HUI" action={<Calendar className="h-3.5 w-3.5 text-copper/70" />}>
            <div className="space-y-2.5">
              {CALENDAR.map((item) => (
                <div key={`${item.time}-${item.title}`} className="flex gap-3">
                  <span className="w-10 shrink-0 font-mono text-[10px] text-copper">{item.time}</span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[11px] text-ivoire/90">{item.title}</p>
                    <StatusBadge status={item.status === "Publié" || item.status === "Envoyée" ? "success" : item.status === "En cours" ? "active" : "warning"}>
                      {item.status}
                    </StatusBadge>
                  </div>
                </div>
              ))}
            </div>
            <button type="button" onClick={() => onNavigateTab("content")} className="mt-3 w-full rounded-lg border border-copper/40 py-1.5 text-[11px] text-copper transition-colors hover:bg-copper/10">
              Voir le calendrier complet
            </button>
          </MockCard>
        </motion.div>
      </div>
    </div>
  );
}
