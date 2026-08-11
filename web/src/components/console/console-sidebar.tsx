"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  AppWindow,
  BookOpen,
  Calculator,
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
  Settings,
  UserRound,
  Scale,
  Users,
  X,
  Zap,
  type LucideIcon,
} from "lucide-react";
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
  decisions: Crown,
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
  legal: Scale,
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

function NavItem({
  href,
  icon,
  label,
  id,
  active,
  badge,
  onClick,
}: {
  href: string;
  icon: ReactNode;
  label: string;
  id?: string;
  active: boolean;
  badge?: number;
  onClick: () => void;
}) {
  return (
    <li>
      <Link
        href={href}
        onClick={onClick}
        className={cn(
          "flex items-center justify-between rounded-md px-3 py-2 text-sm transition-all",
          active
            ? "border border-[#3A251E] bg-[#2A1D18] text-alnua-cuivre"
            : "text-alnua-titane hover:bg-alnua-surface hover:text-alnua-ivoire",
        )}
      >
        <div className="flex items-center gap-3">
          {icon}
          <span>{label}</span>
        </div>
        {badge != null && badge > 0 ? (
          <span className="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-alnua-cuivre/20 px-1.5 text-[10px] font-semibold text-alnua-cuivre">
            {badge > 99 ? "99+" : badge}
          </span>
        ) : id ? (
          <span className="text-xs opacity-50">{id}</span>
        ) : null}
      </Link>
    </li>
  );
}

export function ConsoleSidebar({ mobileOpen, onMobileClose }: ConsoleSidebarProps) {
  const pathname = usePathname();
  const { stats } = useConsoleData();

  const NAV_BADGES: Record<string, number> = {
    decisions: stats.ceoNotifications,
  };

  return (
    <>
      {mobileOpen ? (
        <div
          className="fixed inset-0 z-40 bg-alnua-bg/80 backdrop-blur-sm lg:hidden"
          onClick={onMobileClose}
          aria-hidden
        />
      ) : null}

      <aside
        className={cn(
          "fixed top-0 z-50 flex h-[100dvh] w-64 shrink-0 flex-col justify-between border-r border-alnua-border bg-alnua-bg lg:sticky lg:z-30",
          "transition-transform duration-300 lg:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex min-h-0 flex-1 flex-col">
          <div className="flex h-16 shrink-0 items-center justify-between border-b border-alnua-border px-6">
            <Link
              href={CONSOLE_HOME}
              onClick={onMobileClose}
              className="flex items-center gap-2 font-display text-xl font-bold tracking-widest text-alnua-cuivre"
            >
              <Zap size={20} className="text-alnua-cuivre" aria-hidden />
              ALNUA
            </Link>
            <button
              type="button"
              onClick={onMobileClose}
              className="p-1.5 text-alnua-titane hover:text-alnua-ivoire lg:hidden"
              aria-label="Fermer"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <nav className="alnua-scroll flex-1 space-y-8 overflow-y-auto p-4">
            <div>
              <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-alnua-titane">
                Vue Globale
              </p>
              <ul className="space-y-1">
                {TOP_NAV.map((item) => {
                  const Icon = TOP_ICONS[item.id] ?? LayoutDashboard;
                  const badge =
                    "badge" in item ? NAV_BADGES[item.badge] ?? 0 : undefined;
                  return (
                    <NavItem
                      key={item.id}
                      href={item.href}
                      icon={<Icon size={16} />}
                      label={item.label}
                      active={isActivePath(pathname, item.href)}
                      badge={badge}
                      onClick={onMobileClose}
                    />
                  );
                })}
              </ul>
            </div>

            <div>
              <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-alnua-titane">
                Pôles
              </p>
              <ul className="space-y-1">
                {CONSOLE_POLES.map((pole) => {
                  const Icon = DEPT_ICONS[pole.id] ?? Compass;
                  return (
                    <NavItem
                      key={pole.id}
                      href={pole.href}
                      icon={<Icon size={16} />}
                      label={pole.name.replace("Bureau ", "").replace("Pôle ", "")}
                      id={pole.code}
                      active={isActivePath(pathname, pole.href)}
                      onClick={onMobileClose}
                    />
                  );
                })}
              </ul>
            </div>

            <div>
              <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-alnua-titane">
                Outils
              </p>
              <ul className="space-y-1">
                {TOOL_NAV.map((item) => {
                  const Icon = TOOL_ICONS[item.id] ?? Code2;
                  return (
                    <NavItem
                      key={item.id}
                      href={item.href}
                      icon={<Icon size={16} />}
                      label={item.label}
                      active={isActivePath(pathname, item.href)}
                      onClick={onMobileClose}
                    />
                  );
                })}
              </ul>
            </div>
          </nav>
        </div>

        <div className="shrink-0 border-t border-alnua-border p-4">
          <div className="mb-3 flex items-center gap-3">
            <div
              className="h-8 w-8 rounded-full border border-alnua-cuivre bg-alnua-surface"
              aria-hidden
            />
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-alnua-ivoire">
                Émilie Grade
              </p>
              <p className="text-xs text-alnua-titane">Fondatrice & CEO</p>
            </div>
          </div>
          <Link
            href={ROUTES.settings}
            onClick={onMobileClose}
            className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-[11px] text-alnua-titane transition-colors hover:bg-alnua-surface hover:text-alnua-ivoire"
          >
            <Settings className="h-3.5 w-3.5" />
            Paramètres système
          </Link>
        </div>
      </aside>
    </>
  );
}
