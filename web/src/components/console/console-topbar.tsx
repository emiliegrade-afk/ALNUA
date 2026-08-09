"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import { Bell, Search, Zap } from "lucide-react";
import { useConsoleData } from "./console-provider";
import { consolePathTitle } from "@/lib/console/nav";
import { CONSOLE_POLES } from "@/lib/console/departments";
import { useHubHealthLive } from "@/hooks/use-hub-health-live";
import { useCooStore } from "@/store/coo-store";

interface ConsoleTopbarProps {
  onMobileMenu: () => void;
}

/** Maquette : la topbar porte breadcrumbs + titre + search + clock + bell +
 * bouton "Lancer un agent". Les segments de nav centraux (Vue générale /
 * Départements / Missions / Analytics / Ressources) ont été retirés — ils
 * duppliquaient la sidebar et envoyaient vers des pages héritées (HQ lobby,
 * tickets, analytics dept) qui ne correspondent pas à la maquette. */
function useLiveClock(): Date | null {
  const [now, setNow] = useState<Date | null>(null);
  useEffect(() => {
    const tick = () => setNow(new Date());
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);
  return now;
}

function findPole(pathname: string) {
  return CONSOLE_POLES.find(
    (p) => pathname === p.href || pathname.startsWith(`${p.href}/`),
  );
}

export function ConsoleTopbar({ onMobileMenu }: ConsoleTopbarProps) {
  const pathname = usePathname();
  const { stats } = useConsoleData();
  const { phase } = useHubHealthLive();
  const openDrawer = useCooStore((s) => s.openDrawer);
  const now = useLiveClock();
  const [searchOpen, setSearchOpen] = useState(false);
  const searchRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setSearchOpen((v) => !v);
      }
      if (e.key === "Escape") setSearchOpen(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    if (searchOpen) searchRef.current?.focus();
  }, [searchOpen]);

  const fallback = consolePathTitle(pathname);
  const pole = findPole(pathname);
  const crumb = pole ? "ALNUA / PÔLES" : fallback.crumb;
  const title = pole ? `Pôle ${pole.name.replace("Bureau ", "").replace("Pôle ", "")}` : fallback.title;
  const sub = pole ? pole.tagline : fallback.sub;

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
      <div className="flex h-full items-center gap-4 px-4 sm:px-6">
        {/* Breadcrumbs + titre — maquette : "ALNUA > Vue d'ensemble" + sub-caption */}
        <div className="flex min-w-0 shrink-0 items-center gap-3">
          <button
            type="button"
            onClick={onMobileMenu}
            className="-ml-1 p-2 text-titane hover:text-ivoire lg:hidden"
            aria-label="Menu"
          >
            <span className="text-xl leading-none">≡</span>
          </button>
          <div className="min-w-0">
            <p className="truncate text-[10px] uppercase tracking-[0.2em] text-titane/55">
              {crumb}
            </p>
            <div className="flex items-baseline gap-2">
              <h1 className="truncate font-title text-sm font-semibold tracking-wide text-ivoire sm:text-base">
                {title}
              </h1>
              <span className="hidden truncate text-[11px] text-titane/60 sm:inline">
                {sub}
              </span>
            </div>
          </div>
        </div>

        {/* Search — maquette : barre centrée "Rechercher un agent, un pôle..." + ⌘K */}
        <div className="mx-auto hidden max-w-md flex-1 md:block">
          <button
            type="button"
            onClick={() => setSearchOpen(true)}
            className="flex w-full items-center gap-2 rounded-lg border border-bronze-faint bg-obsidian/60 px-3 py-2 text-xs text-titane/55 transition-colors hover:border-bronze/40 hover:text-titane"
          >
            <Search className="h-3.5 w-3.5 shrink-0" />
            <span className="flex-1 text-left">Rechercher un agent, un pôle…</span>
            <kbd className="rounded border border-bronze-faint bg-obsidian-deep px-1.5 py-0.5 font-mono text-[9px] text-titane/60">
              ⌘K
            </kbd>
          </button>
        </div>

        {/* Droite — clock + bell + "Lancer un agent" */}
        <div className="ml-auto flex items-center gap-2 sm:gap-3">
          <span
            className="hidden font-mono text-xs tabular-nums text-titane/70 lg:inline"
            suppressHydrationWarning
            title={hubLabel}
          >
            {now ? now.toLocaleTimeString("fr-FR", { hour12: false }) : "--:--:--"}
          </span>

          <button
            type="button"
            className="relative rounded-lg border border-bronze-faint bg-obsidian/70 p-2 text-titane transition-colors hover:border-bronze/40 hover:text-bronze-bright"
            aria-label={
              stats.ceoNotifications > 0
                ? `Notifications — ${stats.ceoNotifications} en attente`
                : "Notifications"
            }
          >
            <Bell className="h-4 w-4" />
            {stats.ceoNotifications > 0 ? (
              <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-glow px-1 text-[9px] font-bold text-obsidian-deep">
                {stats.ceoNotifications > 9 ? "9+" : stats.ceoNotifications}
              </span>
            ) : null}
          </button>

          <button
            type="button"
            onClick={() => openDrawer()}
            className="inline-flex items-center gap-1.5 rounded-lg bg-copper px-3 py-2 text-xs font-semibold text-obsidian transition-colors hover:bg-copper-light"
          >
            <Zap className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Lancer un agent</span>
            <span className="sm:hidden">Lancer</span>
          </button>
        </div>
      </div>

      {/* Search modal — ouvert via ⌘K ou clic sur la barre */}
      {searchOpen ? (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center bg-obsidian-deep/70 backdrop-blur-sm"
          onClick={() => setSearchOpen(false)}
        >
          <div
            className="mt-24 w-full max-w-lg rounded-xl border border-bronze-faint bg-obsidian-deep/95 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-3 border-b border-bronze-faint px-4 py-3">
              <Search className="h-4 w-4 text-titane/60" />
              <input
                ref={searchRef}
                type="text"
                placeholder="Rechercher un agent, un pôle…"
                className="flex-1 bg-transparent text-sm text-ivoire placeholder:text-titane/50 focus:outline-none"
              />
              <kbd className="rounded border border-bronze-faint bg-obsidian px-1.5 py-0.5 font-mono text-[9px] text-titane/60">
                ESC
              </kbd>
            </div>
            <div className="max-h-80 overflow-y-auto p-2 alnua-scroll">
              <p className="px-3 py-2 text-[10px] uppercase tracking-widest text-titane/45">
                Pôles
              </p>
              {CONSOLE_POLES.map((p) => (
                <a
                  key={p.id}
                  href={p.href}
                  className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-titane/80 transition-colors hover:bg-obsidian hover:text-ivoire"
                >
                  <span className="font-mono text-[10px] text-titane/40">{p.code}</span>
                  <span className="flex-1">{p.name.replace("Bureau ", "").replace("Pôle ", "")}</span>
                  <span className="truncate text-[11px] text-titane/45">{p.tagline}</span>
                </a>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </header>
  );
}
