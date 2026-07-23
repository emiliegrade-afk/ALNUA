"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import {
  Bell,
  ChevronRight,
  Command,
  Menu,
  MessageCircle,
  Plug,
  Search,
  Zap,
} from "lucide-react";
import { useConsoleData, CONSOLE_POLL_MS } from "./console-provider";
import { consolePathTitle, CONSOLE_AGENTS } from "@/lib/console/nav";
import { ROUTES } from "@/lib/routes";
import { useHubHealthLive } from "@/hooks/use-hub-health-live";
import { useCooStore } from "@/store/coo-store";
import { QuickCaptureTrigger } from "@/components/shared/quick-capture-button";
import { cn } from "@/lib/utils";

interface ConsoleTopbarProps {
  onMobileMenu: () => void;
}

const HUB_PHASE_STYLE = {
  ok: "border-emerald-500/35 text-emerald-300 bg-emerald-500/10",
  checking: "border-white/15 text-titanium/80 bg-white/5",
  key: "border-amber-500/40 text-amber-200 bg-amber-500/10",
  down: "border-red-500/40 text-red-300 bg-red-500/10",
} as const;

export function ConsoleTopbar({ onMobileMenu }: ConsoleTopbarProps) {
  const pathname = usePathname();
  const { stats, departments, lastSyncedAt } = useConsoleData();
  const { phase } = useHubHealthLive();
  const openDrawer = useCooStore((s) => s.openDrawer);
  const dept = departments.find(
    (d) => pathname === d.href || pathname.startsWith(`${d.href}/`),
  );
  const baseTitle = consolePathTitle(pathname);
  const { crumb, title, sub } = dept
    ? {
        crumb: "ALNUA / Pôles",
        title: dept.name,
        sub: dept.tagline,
      }
    : baseTitle;

  const [now, setNow] = useState("");

  useEffect(() => {
    const tick = () => {
      setNow(
        new Date().toLocaleTimeString("fr-FR", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        }),
      );
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  const hubLabel =
    phase === "ok"
      ? "Hub connecté"
      : phase === "checking"
        ? "Sync…"
        : phase === "key"
          ? "Clé API"
          : "Hub offline";

  return (
    <header className="sticky top-0 z-30 h-16 border-b border-bronze-faint bg-obsidian-deep/85 backdrop-blur-xl">
      <div className="flex h-full items-center gap-3 px-4 sm:px-6">
        <button
          type="button"
          onClick={onMobileMenu}
          className="-ml-2 p-2 text-titane hover:text-ivoire lg:hidden"
          aria-label="Menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        {/* min-w floor: without it the fixed-width search + button row crushed
            the page title to 2-3 characters ("B…", "P…") at 1280px. */}
        <div className="min-w-[11rem] flex-[2]">
          <div className="flex items-center gap-1.5 overflow-hidden text-[10px] uppercase tracking-[0.2em] text-titane/45">
            {crumb.split(" / ").map((c, i, arr) => (
              <span key={i} className="flex items-center gap-1.5">
                {i > 0 ? <ChevronRight className="h-3 w-3" /> : null}
                <span className={cn(i === arr.length - 1 && "text-bronze")}>{c}</span>
              </span>
            ))}
          </div>
          <div className="mt-0.5 flex items-baseline gap-2.5">
            <h1 className="truncate text-base font-semibold tracking-wide text-ivoire sm:text-lg">
              {title}
            </h1>
            <span className="hidden truncate text-xs text-titane/55 sm:inline">{sub}</span>
          </div>
        </div>

        <div className="hidden h-9 min-w-[7rem] max-w-72 flex-1 items-center gap-2 rounded-lg border border-bronze-faint bg-obsidian/70 px-3 text-titane/60 transition-colors focus-within:border-bronze/50 md:flex">
          <Search className="h-3.5 w-3.5 shrink-0" />
          <input
            type="text"
            placeholder="Rechercher un agent, un pôle…"
            className="min-w-0 flex-1 bg-transparent text-sm text-ivoire placeholder:text-titane/40 focus:outline-none"
            onFocus={() => {
              window.location.href = CONSOLE_AGENTS;
            }}
            readOnly
          />
          <kbd className="hidden items-center gap-0.5 rounded border border-bronze-faint px-1.5 py-0.5 text-[9px] text-titane/50 lg:inline-flex">
            <Command className="h-2.5 w-2.5" />K
          </kbd>
        </div>

        <Link
          href={ROUTES.connections}
          title="Connexions Composio (Gmail, GitHub…)"
          className={cn(
            "hidden h-9 items-center gap-1.5 rounded-lg border px-3 text-xs font-medium transition-colors sm:inline-flex",
            stats.connectedApps > 0
              ? "border-emerald-500/30 text-emerald-300 hover:border-emerald-500/50"
              : "border-bronze-faint text-titane hover:border-bronze/40 hover:text-bronze-bright",
          )}
        >
          <Plug className="h-3.5 w-3.5" />
          <span className="hidden min-[1440px]:inline">Connexions</span>
          {stats.connectedApps > 0 ? (
            <span className="rounded bg-emerald-500/20 px-1.5 py-0.5 font-mono text-[10px]">
              {stats.connectedApps}
            </span>
          ) : null}
        </Link>

        <div
          className={cn(
            "hidden h-9 items-center gap-2 rounded-lg border px-3 sm:flex",
            HUB_PHASE_STYLE[phase],
          )}
          title={`Dernière sync dashboard · ${CONSOLE_POLL_MS / 1000}s`}
        >
          <span className="relative flex h-1.5 w-1.5">
            {phase === "ok" ? (
              <span className="absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-50 animate-ping" />
            ) : null}
            <span
              className={cn(
                "relative inline-flex h-1.5 w-1.5 rounded-full",
                phase === "ok" && "bg-emerald-400",
                phase === "checking" && "bg-titanium/50",
                phase === "key" && "bg-amber-400",
                phase === "down" && "bg-red-400",
              )}
            />
          </span>
          <span className="text-xs font-medium">{hubLabel}</span>
          <span className="hidden font-mono text-[10px] tabular-nums opacity-70 min-[1440px]:inline">
            {lastSyncedAt
              ? lastSyncedAt.toLocaleTimeString("fr-FR", {
                  hour: "2-digit",
                  minute: "2-digit",
                  second: "2-digit",
                })
              : now}
          </span>
        </div>

        <QuickCaptureTrigger />

        <button
          type="button"
          onClick={openDrawer}
          className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-bronze/40 bg-bronze/10 px-3 text-xs font-semibold text-bronze-bright transition-colors hover:bg-bronze/20"
          aria-label="Ouvrir les assistants Aria et Nadia"
        >
          <MessageCircle className="h-3.5 w-3.5" />
          <span className="hidden min-[1440px]:inline">Assistants</span>
        </button>

        <button
          type="button"
          className="relative rounded-lg border border-bronze-faint bg-obsidian/70 p-2 text-titane transition-colors hover:border-bronze/40 hover:text-bronze-bright"
          aria-label="Notifications"
        >
          <Bell className="h-4 w-4" />
          {stats.ceoNotifications > 0 ? (
            <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-glow" />
          ) : null}
        </button>

        <Link
          href={ROUTES.hub}
          className="hidden h-9 items-center gap-1.5 rounded-lg bg-bronze px-3 text-xs font-semibold text-obsidian-deep transition-colors hover:bg-bronze-bright sm:inline-flex"
        >
          <Zap className="h-3.5 w-3.5" />
          Carte HQ
        </Link>
      </div>
    </header>
  );
}
