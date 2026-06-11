"use client";

import { useEffect, useState } from "react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import { Bell } from "lucide-react";
import Link from "next/link";
import { AlnuaLogo } from "@/components/brand/alnua-logo";
import { DepartmentDoor } from "@/components/lobby/department-door";
import { DEPT_COLORS } from "@/lib/dept-colors";
import { fetchLobbyStats, type LobbyStats } from "@/lib/lobby-api";
import { cn } from "@/lib/utils";

const DEFAULT_STATS: LobbyStats = {
  apiOnline: false,
  ceoNotifications: 0,
  hubPrCount: 0,
  appOpenTickets: 0,
  gamingStatus: "Wyrdheim R&D en cours",
  roboStatus: "Eve — Prototype",
  financesMonthTotal: "$0.00",
  marketingPendingPosts: 0,
  rdSessions: 0,
  brandKits: 0,
  connectedApps: 0,
};

export function LobbyView() {
  const [stats, setStats] = useState<LobbyStats>(DEFAULT_STATS);
  const [loading, setLoading] = useState(true);
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    fetchLobbyStats()
      .then(setStats)
      .catch(() => setStats(DEFAULT_STATS))
      .finally(() => setLoading(false));

    const clock = setInterval(() => setNow(new Date()), 60_000);
    return () => clearInterval(clock);
  }, []);

  const doors = [
    {
      icon: "🏢",
      title: "Bureau du CEO",
      subtitle: "Mission Control · Brief · Décisions en attente",
      description: "1 COO Agent",
      color: DEPT_COLORS.ceo.main,
      href: "/ceo",
      badge:
        stats.ceoNotifications > 0
          ? `${stats.ceoNotifications} notif${stats.ceoNotifications > 1 ? "s" : ""}`
          : "1 COO Agent",
      stats: `1 COO Agent · ${stats.ceoNotifications} notification${stats.ceoNotifications !== 1 ? "s" : ""}`,
    },
    {
      icon: "🏛️",
      title: "Direction",
      subtitle: "Pipeline codage · PM · QA · Spec",
      description: "4 Agents",
      color: DEPT_COLORS.hub.main,
      href: "/hub",
      badge: "4 Agents",
      stats: `4 Agents · ${stats.hubPrCount} PR${stats.hubPrCount !== 1 ? "s" : ""} en attente`,
    },
    {
      icon: "💚",
      title: "Pôle App",
      subtitle: "Naïa App · Eve Journey · Dev · Content",
      description: "2 Agents",
      color: DEPT_COLORS.app.main,
      href: "/app",
      badge: "2 Agents",
      stats: `2 Agents · ${stats.appOpenTickets} ticket${stats.appOpenTickets !== 1 ? "s" : ""} ouvert${stats.appOpenTickets !== 1 ? "s" : ""}`,
    },
    {
      icon: "🎮",
      title: "Pôle Gaming",
      subtitle: "Wyrdheim Online · Naïa World · UE5 · Lore",
      description: "3 Agents",
      color: DEPT_COLORS.gaming.main,
      href: "/gaming",
      badge: "3 Agents",
      stats: stats.gamingStatus,
    },
    {
      icon: "🤖",
      title: "Pôle Robotique",
      subtitle: "Eve Robot · Raspberry Pi · Hardware",
      description: "2 Agents",
      color: DEPT_COLORS.robo.main,
      href: "/robo",
      badge: "2 Agents",
      stats: stats.roboStatus,
    },
    {
      icon: "💰",
      title: "Comptabilité",
      subtitle: "Finances · Coûts LLM · Budget · Transactions",
      description: "Total ce mois",
      color: DEPT_COLORS.finances.main,
      href: "/finances",
      badge: stats.financesMonthTotal,
      stats: `Total ce mois : ${stats.financesMonthTotal}`,
    },
    {
      icon: "📣",
      title: "Marketing",
      subtitle: "Contenu · SEO · Réseaux · Communauté",
      description: "1 Agent",
      color: DEPT_COLORS.marketing.main,
      href: "/marketing",
      badge: "1 Agent",
      stats: `${stats.marketingPendingPosts} post${stats.marketingPendingPosts !== 1 ? "s" : ""} en attente`,
    },
    {
      icon: "🔬",
      title: "R&D",
      subtitle: "Brainstorm · Idées · Sessions · Mémoire",
      description: "1 Agent",
      color: DEPT_COLORS.rd.main,
      href: "/rd",
      badge: "1 Agent",
      stats:
        stats.rdSessions > 0
          ? `${stats.rdSessions} session${stats.rdSessions !== 1 ? "s" : ""} disponibles`
          : "Sessions disponibles",
    },
    {
      icon: "🎨",
      title: "Direction Artistique",
      subtitle: "Brand Kit · Assets · Charte graphique",
      description: "Kits disponibles",
      color: DEPT_COLORS.brand.main,
      href: "/brand",
      badge:
        stats.brandKits > 0
          ? `${stats.brandKits} kit${stats.brandKits !== 1 ? "s" : ""}`
          : undefined,
      stats:
        stats.brandKits > 0
          ? `${stats.brandKits} kit${stats.brandKits !== 1 ? "s" : ""} disponible${stats.brandKits !== 1 ? "s" : ""}`
          : "Kits disponibles",
    },
    {
      icon: "📊",
      title: "Reporting",
      subtitle: "Analytics · KPIs · Métriques · Releases",
      description: "Données disponibles",
      color: DEPT_COLORS.analytics.main,
      href: "/analytics",
      stats: "Données disponibles",
    },
    {
      icon: "🔌",
      title: "IT / Connexions",
      subtitle: "Apps OAuth · Composio · Intégrations",
      description: "Apps connectées",
      color: DEPT_COLORS.it.main,
      href: "/connections",
      badge: `${stats.connectedApps} app${stats.connectedApps !== 1 ? "s" : ""}`,
      stats: `${stats.connectedApps} app${stats.connectedApps !== 1 ? "s" : ""} connectée${stats.connectedApps !== 1 ? "s" : ""}`,
    },
  ];

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-40 border-b border-white/5 bg-obsidian/80 px-6 py-4 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <Link href="/" className="opacity-90 transition hover:opacity-100">
            <AlnuaLogo variant="lockup" height={40} />
          </Link>

          <div className="flex items-center gap-6">
            <div className="hidden text-right sm:block">
              <p className="text-sm font-medium text-white">Bonjour Emilie</p>
              <p className="text-xs text-gray-500">
                {format(now, "EEEE d MMMM yyyy", { locale: fr })}
              </p>
            </div>
            <Link
              href="/ceo"
              className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-gray-400 transition hover:text-white"
              aria-label="Notifications"
            >
              <Bell className="h-4 w-4" />
              {stats.ceoNotifications > 0 ? (
                <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-indigo-500 px-1 text-[10px] font-bold text-white">
                  {stats.ceoNotifications}
                </span>
              ) : null}
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl flex-1 px-6 py-10">
        <div className="mb-10">
          <h1 className="text-3xl font-semibold tracking-tight text-white">
            Siège social ALNUA
          </h1>
          <p className="mt-2 text-gray-400">
            Choisis un département pour entrer dans ton espace de travail.
          </p>
        </div>

        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 11 }).map((_, i) => (
              <div
                key={i}
                className="h-40 animate-pulse rounded-xl bg-white/5"
              />
            ))}
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {doors.map((door) => (
              <DepartmentDoor key={door.href} {...door} />
            ))}
          </div>
        )}
      </main>

      <footer className="border-t border-white/5 px-6 py-4">
        <div className="mx-auto flex max-w-7xl items-center justify-between text-xs text-gray-500">
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "h-2 w-2 rounded-full",
                stats.apiOnline ? "bg-emerald-500" : "bg-red-500"
              )}
            />
            API {stats.apiOnline ? "online" : "offline"}
          </div>
          <span>{format(now, "HH:mm")}</span>
        </div>
      </footer>
    </div>
  );
}
