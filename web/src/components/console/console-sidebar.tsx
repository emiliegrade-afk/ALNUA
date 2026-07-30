"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  Activity,
  AppWindow,
  BookOpen,
  Calculator,
  ChevronRight,
  Code2,
  Compass,
  Crown,
  FileText,
  FlaskConical,
  Gamepad2,
  GraduationCap,
  LayoutDashboard,
  Megaphone,
  Network,
  Palette,
  Scale,
  Settings,
  UserRound,
  Users,
  X,
  type LucideIcon,
} from "lucide-react";
import { AlnuaLogo } from "./alnua-logo";
import { AlnuaCoreWidget } from "./alnua-core-widget";
import { useConsoleData } from "./console-provider";
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
  decisions: Scale,
};

const TOOL_ICONS: Record<string, LucideIcon> = {
  docs: FileText,
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

/** Cadre commun aux trois sections de nav (maquette de référence). */
const SECTION_BOX =
  "space-y-0.5 rounded-[10px] border border-copper/15 bg-obsidian-2/50 p-2";

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
  const { stats } = useConsoleData();

  // Compteurs live des entrées à badge (maquette : « Décisions · 2 »).
  const NAV_BADGES: Record<string, number> = {
    decisions: stats.ceoNotifications,
  };

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
          "fixed top-0 z-50 flex h-[100dvh] w-[244px] shrink-0 flex-col border-r border-bronze-faint bg-obsidian-deep lg:sticky lg:z-30",
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

        {/* Maquette : chaque section est un bloc encadré posé sur un fond
            légèrement plus clair que la sidebar, pas une liste à plat. */}
        <nav className="alnua-scroll flex-1 space-y-3 overflow-y-auto px-3 py-4">
          <div className={SECTION_BOX}>
            <p className="mb-2 ml-2 mt-0.5 text-[8.5px] uppercase tracking-[0.2em] text-titane/55">
              Tableau de bord
            </p>
            {TOP_NAV.map((item) => {
              const Icon = TOP_ICONS[item.id] ?? LayoutDashboard;
              const active = isActivePath(pathname, item.href);
              const badge = "badge" in item ? NAV_BADGES[item.badge] ?? 0 : 0;
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
                  <span className="flex-1 font-medium">{item.label}</span>
                  {badge > 0 ? (
                    <span className="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-bronze/20 px-1.5 text-[10px] font-semibold text-bronze-bright">
                      {badge > 99 ? "99+" : badge}
                    </span>
                  ) : null}
                </Link>
              );
            })}
          </div>

          <div className={SECTION_BOX}>
            <p className="mb-2 ml-2 mt-0.5 text-[8.5px] uppercase tracking-[0.2em] text-titane/55">
              Départements · {CONSOLE_POLES.length}
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
                  <span
                    className={cn(
                      "shrink-0 font-mono text-[10px] tabular-nums",
                      active ? "text-bronze-bright/80" : "text-titane/35",
                    )}
                  >
                    {pole.code}
                  </span>
                  <Icon className="h-3.5 w-3.5 shrink-0" />
                  <span className="flex-1 truncate text-left font-medium">
                    {pole.name.replace("Bureau ", "").replace("Pôle ", "")}
                  </span>
                  <ChevronRight
                    className={cn(
                      "h-3.5 w-3.5 shrink-0 transition-transform",
                      active
                        ? "text-bronze-bright"
                        : "text-titane/25 group-hover:translate-x-0.5 group-hover:text-titane/50",
                    )}
                  />
                </Link>
              );
            })}
          </div>

          <div className={SECTION_BOX}>
            <p className="mb-2 ml-2 mt-0.5 text-[8.5px] uppercase tracking-[0.2em] text-titane/55">
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

        <div className="shrink-0 space-y-2 border-t border-bronze-faint p-4">
          <AlnuaCoreWidget />
          <Link
            href={ROUTES.settings}
            onClick={onMobileClose}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-[11px] text-titane/60 transition-colors hover:bg-obsidian hover:text-ivoire"
          >
            <Settings className="h-3.5 w-3.5" />
            Paramètres système
          </Link>
        </div>
      </aside>
    </>
  );
}
