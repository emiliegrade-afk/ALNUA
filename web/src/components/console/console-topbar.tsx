"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bell, Search, Zap } from "lucide-react";
import { useConsoleData } from "./console-provider";
import { consolePathTitle } from "@/lib/console/nav";
import { CONSOLE_POLES } from "@/lib/console/departments";
import { useHubHealthLive } from "@/hooks/use-hub-health-live";
import { useCooStore } from "@/store/coo-store";
import { cn } from "@/lib/utils";

interface ConsoleTopbarProps {
  onMobileMenu: () => void;
}

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
  const title = pole
    ? `Pôle ${pole.name.replace("Bureau ", "").replace("Pôle ", "")}`
    : fallback.title;
  const sub = pole ? pole.tagline : fallback.sub;

  const hubOk = phase === "ok";
  const hubLabel =
    phase === "ok"
      ? "Hub connecté"
      : phase === "checking"
        ? "Sync…"
        : phase === "key"
          ? "Clé API"
          : "Hub offline";

  const clock =
    now?.toLocaleTimeString("fr-FR", { hour12: false }) ?? "--:--:--";

  return (
    <header className="sticky top-0 z-30 h-16 border-b border-titanium/20 bg-void/95">
      <div className="flex h-full items-center justify-between gap-4 px-4 sm:px-8">
        <div className="flex min-w-0 items-center gap-4">
          <button
            type="button"
            onClick={onMobileMenu}
            className="-ml-1 p-2 text-metal-titanium hover:text-ivoire lg:hidden"
            aria-label="Menu"
          >
            <span className="text-xl leading-none">≡</span>
          </button>
          <h1 className="truncate font-display text-lg uppercase tracking-wide text-ivoire">
            {title}
            <span className="ml-2 hidden text-sm font-sans font-normal normal-case tracking-normal text-metal-titanium sm:inline">
              {sub}
            </span>
          </h1>
        </div>

        <div className="flex items-center gap-3 sm:gap-4">
          <div className="relative hidden md:block">
            <Search
              size={16}
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-alnua-titane"
              aria-hidden
            />
            <input
              type="text"
              readOnly
              onFocus={() => setSearchOpen(true)}
              onClick={() => setSearchOpen(true)}
              placeholder="Rechercher... (⌘K)"
              className="w-64 rounded-full border border-alnua-border bg-alnua-surface py-1.5 pl-10 pr-4 text-sm text-alnua-ivoire placeholder:text-alnua-titane transition-colors focus:border-alnua-cuivre focus:outline-none"
              aria-label="Rechercher"
            />
          </div>

          <div
            className={cn(
              "hidden items-center gap-2 rounded-full border px-3 py-1.5 sm:flex",
              hubOk
                ? "border-[#103020] bg-alnua-surface"
                : "border-alnua-danger/40 bg-alnua-surface",
            )}
            title={hubLabel}
          >
            <div
              className={cn(
                "h-2 w-2 rounded-full",
                hubOk ? "animate-pulse bg-alnua-teal" : "bg-alnua-danger",
              )}
            />
            <span
              className={cn(
                "text-xs font-medium tabular-nums",
                hubOk ? "text-alnua-teal" : "text-alnua-danger",
              )}
              suppressHydrationWarning
            >
              {hubLabel} {hubOk ? clock : null}
            </span>
          </div>

          <button
            type="button"
            className="relative rounded-full border border-alnua-border p-2 text-alnua-cuivre transition-colors hover:bg-alnua-surface"
            aria-label={
              stats.ceoNotifications > 0
                ? `Notifications — ${stats.ceoNotifications} en attente`
                : "Notifications"
            }
          >
            <Bell size={18} />
            {stats.ceoNotifications > 0 ? (
              <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-alnua-cuivre px-1 text-[9px] font-bold text-alnua-bg">
                {stats.ceoNotifications > 9 ? "9+" : stats.ceoNotifications}
              </span>
            ) : null}
          </button>

          <button
            type="button"
            onClick={() => openDrawer()}
            className="inline-flex items-center gap-1.5 rounded-full border border-alnua-cuivre/40 bg-alnua-cuivre/10 px-3 py-1.5 text-xs font-semibold text-alnua-cuivre transition-colors hover:bg-alnua-cuivre/20"
          >
            <Zap className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Lancer un agent</span>
          </button>
        </div>
      </div>

      {searchOpen ? (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center bg-alnua-bg/70 backdrop-blur-sm"
          onClick={() => setSearchOpen(false)}
        >
          <div
            className="mt-24 w-full max-w-lg rounded-xl border border-alnua-border bg-alnua-surface shadow-2xl"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-label="Recherche"
          >
            <div className="flex items-center gap-3 border-b border-alnua-border px-4 py-3">
              <Search className="h-4 w-4 text-alnua-titane" />
              <input
                ref={searchRef}
                type="text"
                placeholder="Rechercher un agent, un pôle…"
                className="flex-1 bg-transparent text-sm text-alnua-ivoire placeholder:text-alnua-titane focus:outline-none"
              />
              <kbd className="rounded border border-alnua-border bg-alnua-bg px-1.5 py-0.5 font-mono text-[9px] text-alnua-titane">
                ESC
              </kbd>
            </div>
            <div className="alnua-scroll max-h-80 overflow-y-auto p-2">
              <p className="px-3 py-2 text-[10px] uppercase tracking-widest text-alnua-titane/60">
                Pôles
              </p>
              {CONSOLE_POLES.map((p) => (
                <Link
                  key={p.id}
                  href={p.href}
                  onClick={() => setSearchOpen(false)}
                  className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-alnua-titane transition-colors hover:bg-alnua-bg hover:text-alnua-ivoire"
                >
                  <span className="font-mono text-[10px] text-alnua-titane/50">
                    {p.code}
                  </span>
                  <span className="flex-1">
                    {p.name.replace("Bureau ", "").replace("Pôle ", "")}
                  </span>
                  <span className="truncate text-[11px] text-alnua-titane/45">
                    {p.tagline}
                  </span>
                </Link>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </header>
  );
}
