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

export function MockupMarketingView({ department }: MarketingViewProps) {
  void department;
  const [tab, setTab] = useState("vue");
  const panel = MARKETING_SECONDARY[tab];

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
