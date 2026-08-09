"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bell, Map, Plus, Search, Sparkles } from "lucide-react";
import { useConsoleData } from "@/components/console/console-provider";
import { useHubHealthLive } from "@/hooks/use-hub-health-live";
import { useCooStore } from "@/store/coo-store";
import { CONSOLE_POLES } from "@/lib/console/departments";
import { consolePathTitle } from "@/lib/console/nav";
import { cn } from "@/lib/utils";

interface MockupTopbarProps {
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

function poleDisplayTitle(poleName: string): string {
  const clean = poleName.replace("Bureau ", "").replace("Pôle ", "");
  if (clean.toLowerCase().includes("compta")) return "PÔLE COMPTABILITÉ";
  return `PÔLE ${clean.toUpperCase()}`;
}

export function MockupTopbar({ onMobileMenu }: MockupTopbarProps) {
  const pathname = usePathname();
  const { stats, activeAgents } = useConsoleData();
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
  const title = pole ? poleDisplayTitle(pole.name) : fallback.title;
  const sub = pole ? pole.tagline.replace(/·/g, "·") : fallback.sub;
  const isPolePage = Boolean(pole);

  const hubOk = phase === "ok";
  const hubLabel = hubOk ? "Hub connecté" : phase === "checking" ? "Sync…" : "Hub offline";
  const timeLabel = now
    ? now.toLocaleTimeString("fr-FR", { hour12: false })
    : "--:--:--";

  return (
    <header className="sticky top-0 z-30 shrink-0 border-b border-bronze-faint bg-obsidian-deep/90 backdrop-blur-xl">
      <div className="flex h-[4.25rem] items-center gap-3 px-4 sm:gap-4 sm:px-6">
        <button
          type="button"
          onClick={onMobileMenu}
          className="-ml-1 p-2 text-titane transition-colors hover:text-ivoire lg:hidden"
          aria-label="Menu"
        >
          <span className="text-xl leading-none">≡</span>
        </button>

        <div className="flex min-w-0 shrink-0 flex-col justify-center">
          <h1
            className={cn(
              "truncate font-title text-sm font-semibold tracking-[0.06em] sm:text-base",
              isPolePage ? "text-copper" : "text-ivoire",
            )}
          >
            {title}
          </h1>
          <p className="hidden truncate text-[11px] text-titane/55 sm:block">{sub}</p>
        </div>

        <div className="mx-auto hidden max-w-sm flex-1 lg:block xl:max-w-md">
          <button
            type="button"
            onClick={() => setSearchOpen(true)}
            className="flex w-full items-center gap-2 rounded-full border border-bronze-faint bg-obsidian/60 px-4 py-2 text-xs text-titane/55 transition-all duration-200 hover:border-bronze/40 hover:text-titane"
          >
            <Search className="h-3.5 w-3.5 shrink-0" />
            <span className="flex-1 text-left">Rechercher… (⌘K)</span>
          </button>
        </div>

        <div className="ml-auto flex items-center gap-2 sm:gap-2.5">
          <div className="hidden items-center gap-2 md:flex">
            <StatusPill
              label="Connexions"
              value={String(Math.max(activeAgents, 1))}
              ok
            />
            <StatusPill
              label={hubLabel}
              value={timeLabel}
              ok={hubOk}
              mono
            />
          </div>

          <button
            type="button"
            onClick={() => openDrawer()}
            className="hidden items-center gap-1.5 rounded-lg border border-copper/40 px-3 py-1.5 text-xs font-medium text-copper transition-all duration-200 hover:bg-copper/10 sm:inline-flex"
          >
            <Plus className="h-3.5 w-3.5" />
            Créer
          </button>

          <button
            type="button"
            onClick={() => openDrawer()}
            className="hidden items-center gap-1.5 rounded-lg border border-copper/40 px-3 py-1.5 text-xs font-medium text-copper transition-all duration-200 hover:bg-copper/10 lg:inline-flex"
          >
            <Sparkles className="h-3.5 w-3.5" />
            Assistants
          </button>

          <button
            type="button"
            className="relative rounded-lg border border-bronze-faint bg-obsidian/70 p-2 text-titane transition-all duration-200 hover:border-bronze/40 hover:text-bronze-bright"
            aria-label={
              stats.ceoNotifications > 0
                ? `Notifications — ${stats.ceoNotifications}`
                : "Notifications"
            }
          >
            <Bell className="h-4 w-4" />
            {stats.ceoNotifications > 0 ? (
              <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-copper px-1 text-[9px] font-bold text-obsidian-deep">
                {stats.ceoNotifications > 9 ? "9+" : stats.ceoNotifications}
              </span>
            ) : null}
          </button>

          <Link
            href="/hq"
            className="hidden items-center gap-1.5 rounded-lg border border-copper/50 px-3 py-1.5 text-xs font-semibold text-copper transition-all duration-200 hover:bg-copper/10 xl:inline-flex"
          >
            <Map className="h-3.5 w-3.5" />
            Carte HQ
          </Link>
        </div>
      </div>

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
            <div className="alnua-scroll max-h-80 overflow-y-auto p-2">
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
                  <span className="flex-1">
                    {p.name.replace("Bureau ", "").replace("Pôle ", "")}
                  </span>
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

function StatusPill({
  label,
  value,
  ok,
  mono,
}: {
  label: string;
  value: string;
  ok?: boolean;
  mono?: boolean;
}) {
  return (
    <div className="flex items-center gap-1.5 rounded-full border border-bronze-faint bg-obsidian/50 px-2.5 py-1 text-[10px]">
      <span
        className={cn(
          "h-1.5 w-1.5 rounded-full",
          ok ? "bg-online shadow-[0_0_6px_rgba(34,197,94,0.7)]" : "bg-copper",
        )}
      />
      <span className="text-titane/60">{label}</span>
      <span
        className={cn(
          "font-medium text-ivoire/85",
          mono && "font-mono tabular-nums",
        )}
        suppressHydrationWarning
      >
        {value}
      </span>
    </div>
  );
}
