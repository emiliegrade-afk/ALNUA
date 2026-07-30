"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Bell,
  BookOpen,
  ChevronDown,
  KanbanSquare,
  LayoutGrid,
  Map,
  Menu,
  MessageCircle,
  Plug,
  Rows3,
  Search,
  Settings,
  type LucideIcon,
} from "lucide-react";
import { useConsoleData, CONSOLE_POLL_MS } from "./console-provider";
import { Sparkline } from "./charts";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { CONSOLE_AGENTS } from "@/lib/console/nav";
import { CONSOLE_POLES } from "@/lib/console/departments";
import { HUB_OWNER, HUB_CHIEF } from "@/lib/console/owner";
import { ROUTES } from "@/lib/routes";
import { useHubHealthLive } from "@/hooks/use-hub-health-live";
import { useCooStore } from "@/store/coo-store";
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

/** Nav segmentée centrale des maquettes. Chaque entrée mène à une vue réelle —
 * "Départements" pointe vers le plan des bureaux et s'allume aussi sur
 * n'importe quelle page de pôle (c'est là qu'on se trouve en la lisant). */
const SEGMENTS: { id: string; label: string; href: string; icon: LucideIcon }[] = [
  { id: "overview", label: "Vue générale", href: ROUTES.home, icon: Rows3 },
  { id: "departments", label: "Départements", href: ROUTES.hq, icon: LayoutGrid },
  { id: "missions", label: "Missions", href: ROUTES.tickets, icon: KanbanSquare },
  { id: "analytics", label: "Analytics", href: ROUTES.analytics, icon: BarChart3 },
  { id: "resources", label: "Ressources", href: ROUTES.library, icon: BookOpen },
];

const POLE_HREFS = CONSOLE_POLES.map((p) => p.href);

function activeSegment(pathname: string): string {
  if (pathname === ROUTES.home) return "overview";
  if (POLE_HREFS.some((h) => pathname === h || pathname.startsWith(`${h}/`))) {
    return "departments";
  }
  const match = SEGMENTS.find(
    (s) => s.id !== "overview" && (pathname === s.href || pathname.startsWith(`${s.href}/`)),
  );
  return match?.id ?? "";
}

export function ConsoleTopbar({ onMobileMenu }: ConsoleTopbarProps) {
  const pathname = usePathname();
  const { stats, activity24h, liveAgents, lastSyncedAt } = useConsoleData();
  const { phase } = useHubHealthLive();
  const openDrawer = useCooStore((s) => s.openDrawer);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const current = activeSegment(pathname);
  const chiefStatus = liveAgents[HUB_CHIEF.agentId]?.status ?? "idle";
  const chiefOnline = chiefStatus === "working" || chiefStatus === "waiting";

  useEffect(() => {
    if (!menuOpen) return;
    function onDown(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setMenuOpen(false);
    }
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [menuOpen]);

  useEffect(() => {
    setMenuOpen(false);
  }, [pathname]);

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

        {/* Identité du chef d'orchestre — présence permanente des maquettes */}
        <Link
          href={ROUTES.hub}
          className="group flex min-w-0 shrink-0 items-center gap-2.5"
          title={`${HUB_CHIEF.role} — ${HUB_CHIEF.name}`}
        >
          <AgentAvatar
            agentId={HUB_CHIEF.agentId}
            name={HUB_CHIEF.name}
            size={38}
            ring
            className="hidden sm:inline-flex"
          />
          <span className="min-w-0">
            <span className="flex items-baseline gap-1.5">
              <span className="text-[11px] uppercase tracking-[0.18em] text-titane/50">
                {HUB_CHIEF.shortRole}
              </span>
              <span className="truncate text-sm font-semibold text-ivoire group-hover:text-bronze-bright">
                {HUB_CHIEF.name}
              </span>
            </span>
            <span className="mt-0.5 flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-bronze-faint bg-obsidian/60 px-1.5 py-px text-[9px] text-titane/65">
                <span
                  className={cn(
                    "h-1.5 w-1.5 rounded-full",
                    chiefOnline ? "bg-bronze-bright" : "bg-titane/40",
                  )}
                />
                {chiefOnline ? "En ligne" : "En veille"}
              </span>
              {activity24h.length > 1 ? (
                <Sparkline
                  data={activity24h}
                  width={72}
                  height={14}
                  fill={false}
                  strokeWidth={1}
                  className="hidden opacity-70 min-[1180px]:block"
                />
              ) : null}
            </span>
          </span>
        </Link>

        {/* Nav segmentée centrale */}
        <nav
          aria-label="Sections principales"
          className="mx-auto hidden items-center gap-1 rounded-xl border border-bronze-faint bg-obsidian/50 p-1 md:flex"
        >
          {SEGMENTS.map((seg) => {
            const Icon = seg.icon;
            const active = current === seg.id;
            return (
              <Link
                key={seg.id}
                href={seg.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors",
                  active
                    ? "border border-bronze/40 bg-bronze/12 text-bronze-bright"
                    : "border border-transparent text-titane/70 hover:bg-obsidian-deep hover:text-ivoire",
                )}
              >
                <Icon className="h-3.5 w-3.5 shrink-0" />
                <span className="hidden lg:inline">{seg.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Maquette : à droite, la cloche et la carte profil, rien d'autre —
            recherche, capture et assistants vivent dans le menu profil et la
            barre d'action basse, sinon la nav centrale se fait écraser. */}
        <div className="ml-auto flex items-center gap-2">
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

          {/* Carte profil — replie Connexions / statut Hub / Carte HQ */}
          <div className="relative" ref={menuRef}>
            <button
              type="button"
              onClick={() => setMenuOpen((v) => !v)}
              aria-expanded={menuOpen}
              aria-haspopup="menu"
              className={cn(
                "flex h-11 items-center gap-2.5 rounded-xl border px-2 transition-colors",
                menuOpen
                  ? "border-bronze/40 bg-bronze/10"
                  : "border-bronze-faint bg-obsidian/70 hover:border-bronze/30",
              )}
            >
              <AgentAvatar agentId={HUB_OWNER.id} name={HUB_OWNER.name} size={30} />
              <span className="hidden text-left leading-tight min-[1240px]:block">
                <span className="block text-xs font-semibold text-ivoire">{HUB_OWNER.name}</span>
                <span className="block text-[10px] text-titane/55">{HUB_OWNER.role}</span>
              </span>
              <ChevronDown
                className={cn(
                  "h-3.5 w-3.5 shrink-0 text-titane/50 transition-transform",
                  menuOpen && "rotate-180",
                )}
              />
            </button>

            {menuOpen ? (
              <div
                role="menu"
                className="absolute right-0 top-[calc(100%+0.5rem)] w-64 overflow-hidden rounded-xl border border-bronze-faint bg-obsidian-deep/95 shadow-[0_16px_48px_rgba(0,0,0,0.6)] backdrop-blur-xl"
              >
                <div className="border-b border-bronze-faint px-4 py-3">
                  <p className="text-sm font-semibold text-ivoire">{HUB_OWNER.name}</p>
                  <p className="text-[11px] text-titane/55">{HUB_OWNER.role}</p>
                </div>

                <div
                  className={cn(
                    "mx-3 my-3 flex items-center gap-2 rounded-lg border px-3 py-2",
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
                  {lastSyncedAt ? (
                    <span className="ml-auto font-mono text-[10px] tabular-nums opacity-70">
                      {lastSyncedAt.toLocaleTimeString("fr-FR", {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  ) : null}
                </div>

                <div className="pb-2">
                  <button
                    type="button"
                    role="menuitem"
                    onClick={() => {
                      setMenuOpen(false);
                      openDrawer();
                    }}
                    className="flex w-full items-center gap-2.5 px-4 py-2.5 text-left text-xs text-titane/75 transition-colors hover:bg-obsidian hover:text-ivoire"
                  >
                    <MessageCircle className="h-3.5 w-3.5 shrink-0" />
                    Assistants — Aria &amp; Nadia
                  </button>
                  <Link
                    href={CONSOLE_AGENTS}
                    role="menuitem"
                    className="flex items-center gap-2.5 px-4 py-2.5 text-xs text-titane/75 transition-colors hover:bg-obsidian hover:text-ivoire"
                  >
                    <Search className="h-3.5 w-3.5 shrink-0" />
                    Rechercher un agent
                  </Link>
                  <Link
                    href={ROUTES.connections}
                    role="menuitem"
                    className="flex items-center gap-2.5 px-4 py-2.5 text-xs text-titane/75 transition-colors hover:bg-obsidian hover:text-ivoire"
                  >
                    <Plug className="h-3.5 w-3.5 shrink-0" />
                    Connexions
                    {stats.connectedApps > 0 ? (
                      <span className="ml-auto rounded bg-emerald-500/20 px-1.5 py-0.5 font-mono text-[10px] text-emerald-300">
                        {stats.connectedApps}
                      </span>
                    ) : null}
                  </Link>
                  <Link
                    href={ROUTES.hq}
                    role="menuitem"
                    className="flex items-center gap-2.5 px-4 py-2.5 text-xs text-titane/75 transition-colors hover:bg-obsidian hover:text-ivoire"
                  >
                    <Map className="h-3.5 w-3.5 shrink-0" />
                    Carte HQ
                  </Link>
                  <Link
                    href={ROUTES.settings}
                    role="menuitem"
                    className="flex items-center gap-2.5 px-4 py-2.5 text-xs text-titane/75 transition-colors hover:bg-obsidian hover:text-ivoire"
                  >
                    <Settings className="h-3.5 w-3.5 shrink-0" />
                    Paramètres système
                  </Link>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </header>
  );
}
