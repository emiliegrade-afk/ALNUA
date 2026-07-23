"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  Activity,
  AppWindow,
  BookOpen,
  Calculator,
  Code2,
  Compass,
  Crown,
  FlaskConical,
  Gamepad2,
  GraduationCap,
  LayoutDashboard,
  Map,
  Megaphone,
  Network,
  Palette,
  Settings,
  UserRound,
  Users,
  X,
  type LucideIcon,
} from "lucide-react";
import { AlnuaLogo } from "./alnua-logo";
import { useConsoleData } from "./console-provider";
import { useHubHealthLive } from "@/hooks/use-hub-health-live";
import { CONSOLE_POLES } from "@/lib/console/departments";
import { ROUTES } from "@/lib/routes";
import {
  CONSOLE_HOME,
  TOOL_NAV,
  TOP_NAV,
} from "@/lib/console/nav";
import { cn } from "@/lib/utils";

const TOP_ICONS: Record<string, LucideIcon> = {
  dashboard: LayoutDashboard,
  agents: Users,
  activity: Activity,
  hq: Map,
};

const TOOL_ICONS: Record<string, LucideIcon> = {
  ide: Code2,
  academy: GraduationCap,
  library: BookOpen,
};

const DEPT_ICONS: Record<string, LucideIcon> = {
  hub: Compass,
  secretary: UserRound,
  ceo: Crown,
  rd: FlaskConical,
  app: AppWindow,
  gaming: Gamepad2,
  robo: Network,
  marketing: Megaphone,
  finances: Calculator,
  analytics: Compass,
  brand: Palette,
};

interface ConsoleSidebarProps {
  mobileOpen: boolean;
  onMobileClose: () => void;
}

function isActivePath(pathname: string, href: string): boolean {
  if (href === CONSOLE_HOME) return pathname === CONSOLE_HOME;
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function ConsoleSidebar({ mobileOpen, onMobileClose }: ConsoleSidebarProps) {
  const pathname = usePathname();
  const { activeAgents, totalAgents, stats } = useConsoleData();
  // Same live probe as the topbar badge — the aggregated lobby stats lag by
  // up to their cache TTL, which made this row say "Hors ligne" while the
  // topbar said "Hub connecté".
  const { phase: hubPhase } = useHubHealthLive();

  return (
    <>
      {mobileOpen ? (
        <div
          className="fixed inset-0 z-40 bg-obsidian-deep/80 backdrop-blur-sm lg:hidden"
          onClick={onMobileClose}
          aria-hidden
        />
      ) : null}

      <aside
        className={cn(
          "fixed top-0 z-50 flex h-[100dvh] w-[270px] shrink-0 flex-col border-r border-bronze-faint bg-obsidian-deep lg:sticky lg:z-30",
          "transition-transform duration-300 lg:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex h-16 shrink-0 items-center justify-between gap-2 border-b border-bronze-faint px-5">
          <Link
            href={CONSOLE_HOME}
            onClick={onMobileClose}
            className="group flex items-center gap-3"
          >
            <AlnuaLogo variant="icon" size={32} staticMark />
            <div className="flex flex-col leading-none text-left">
              <span className="text-base font-bold tracking-[0.28em] text-gradient-bronze">
                ALNUA
              </span>
              <span className="mt-0.5 text-[8px] tracking-[0.32em] text-titane/55">
                VIRTUAL AI ENTERPRISE
              </span>
            </div>
          </Link>
          <button
            type="button"
            onClick={onMobileClose}
            className="p-1.5 text-titane hover:text-ivoire lg:hidden"
            aria-label="Fermer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="alnua-scroll flex-1 space-y-6 overflow-y-auto px-3 py-4">
          <div className="space-y-1">
            <p className="mb-2 px-3 text-[9px] uppercase tracking-[0.25em] text-titane/40">
              Navigation
            </p>
            {TOP_NAV.map((item) => {
              const Icon = TOP_ICONS[item.id] ?? LayoutDashboard;
              const active = isActivePath(pathname, item.href);
              return (
                <Link
                  key={item.id}
                  href={item.href}
                  onClick={onMobileClose}
                  className={cn(
                    "relative flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                    active
                      ? "bg-bronze/10 text-bronze-bright"
                      : "text-titane/75 hover:bg-obsidian hover:text-ivoire",
                  )}
                >
                  {active ? (
                    <motion.span
                      layoutId="console-nav-active"
                      className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-full bg-bronze"
                      transition={{ type: "spring", stiffness: 400, damping: 32 }}
                    />
                  ) : null}
                  <Icon className="h-4 w-4 shrink-0" />
                  <span className="font-medium">{item.label}</span>
                </Link>
              );
            })}
          </div>

          <div className="space-y-1">
            <p className="mb-2 px-3 text-[9px] uppercase tracking-[0.25em] text-titane/40">
              Pôles · {CONSOLE_POLES.length}
            </p>
            {CONSOLE_POLES.map((pole) => {
              const Icon = DEPT_ICONS[pole.id] ?? Compass;
              const active = isActivePath(pathname, pole.href);
              return (
                <Link
                  key={pole.id}
                  href={pole.href}
                  onClick={onMobileClose}
                  className={cn(
                    "group relative flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                    active
                      ? "bg-bronze/10 text-bronze-bright"
                      : "text-titane/70 hover:bg-obsidian hover:text-ivoire",
                  )}
                >
                  {active ? (
                    <motion.span
                      layoutId="console-nav-active"
                      className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-full bg-bronze"
                      transition={{ type: "spring", stiffness: 400, damping: 32 }}
                    />
                  ) : null}
                  <Icon className="h-3.5 w-3.5 shrink-0" />
                  <span className="flex-1 truncate text-left font-medium">
                    {pole.name.replace("Bureau ", "").replace("Pôle ", "")}
                  </span>
                  <span className="font-mono text-[9px] text-titane/35">{pole.code}</span>
                  <span className="h-1.5 w-1.5 rounded-full bg-bronze-bright/80" />
                </Link>
              );
            })}
          </div>

          <div className="space-y-1">
            <p className="mb-2 px-3 text-[9px] uppercase tracking-[0.25em] text-titane/40">
              Outils
            </p>
            {TOOL_NAV.map((item) => {
              const Icon = TOOL_ICONS[item.id] ?? Code2;
              const active = isActivePath(pathname, item.href);
              return (
                <Link
                  key={item.id}
                  href={item.href}
                  onClick={onMobileClose}
                  className={cn(
                    "relative flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                    active
                      ? "bg-bronze/10 text-bronze-bright"
                      : "text-titane/75 hover:bg-obsidian hover:text-ivoire",
                  )}
                >
                  {active ? (
                    <motion.span
                      layoutId="console-nav-active"
                      className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-full bg-bronze"
                      transition={{ type: "spring", stiffness: 400, damping: 32 }}
                    />
                  ) : null}
                  <Icon className="h-4 w-4 shrink-0" />
                  <span className="font-medium">{item.label}</span>
                </Link>
              );
            })}
          </div>
        </nav>

        <div className="shrink-0 space-y-2.5 border-t border-bronze-faint p-4">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-titane/60">Agents en ligne</span>
            <span className="inline-flex items-center gap-1.5 text-ivoire">
              <span className="h-1.5 w-1.5 animate-alnua-pulse rounded-full bg-bronze-bright" />
              {activeAgents} / {totalAgents}
            </span>
          </div>
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-titane/60">API Hub</span>
            <span
              className={
                hubPhase === "ok" || hubPhase === "key"
                  ? "text-bronze-bright"
                  : hubPhase === "checking"
                    ? "text-titane/60"
                    : "text-red-400"
              }
            >
              {hubPhase === "ok" || hubPhase === "key"
                ? "En ligne"
                : hubPhase === "checking"
                  ? "Sync…"
                  : "Hors ligne"}
            </span>
          </div>
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-titane/60">Coût / jour</span>
            <span className="text-ivoire">${stats.costTodayUsd.toFixed(2)}</span>
          </div>
          <Link
            href={ROUTES.settings}
            onClick={onMobileClose}
            className="mt-2 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-[11px] text-titane/60 transition-colors hover:bg-obsidian hover:text-ivoire"
          >
            <Settings className="h-3.5 w-3.5" />
            Paramètres système
          </Link>
        </div>
      </aside>
    </>
  );
}
