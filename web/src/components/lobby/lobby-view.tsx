"use client";

import { Suspense, useEffect, useState } from "react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import { Bell, MoreHorizontal, Settings } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AlnuaLogo } from "@/components/brand/alnua-logo";
import { useHubNavigate } from "@/components/layout/hub-navigation";
import { HqActivityMonitorPanel } from "@/components/lobby/hq-activity-monitor-panel";
import { HqAgentPanel } from "@/components/lobby/hq-agent-panel";
import { HqHubMap } from "@/components/lobby/hq-hub-map";
import {
  fetchLobbyStats,
  getLobbyStatsCache,
  type LobbyStats,
} from "@/lib/lobby-api";
import { type HqSector } from "@/lib/hq-hub-offices";
import {
  countActiveAgents,
  fetchAgentsStatus,
  type AgentStatus,
  type OpenRoomLogEntry,
} from "@/lib/openroom-api";
import { prefetchAllOfficeRoutes } from "@/lib/hq-prefetch";
import { cn } from "@/lib/utils";
import {
  ADMIN_LINKS,
  fetchAdminFlags,
  isAdminPageEnabled,
  withAdminPreview,
  type AdminFlags,
} from "@/lib/admin-flags-api";

const STATIC_ADMIN_LINKS = [
  { href: "/briefing", label: "Briefing" },
  { href: "/openroom", label: "OpenRoom" },
  { href: "/beta", label: "Beta" },
  { href: "/waitlist", label: "Waitlist" },
  { href: "/releases", label: "Releases" },
  { href: "/partnerships/manage", label: "Partenariats" },
] as const;

const DEFAULT_STATS: LobbyStats = {
  apiOnline: false,
  apiAuthenticated: false,
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
  const router = useRouter();
  const { navigate } = useHubNavigate();
  const [stats, setStats] = useState<LobbyStats>(DEFAULT_STATS);
  const [agents, setAgents] = useState<Record<string, AgentStatus>>({});
  const [recentLogs, setRecentLogs] = useState<OpenRoomLogEntry[]>([]);
  const [activeAgents, setActiveAgents] = useState(0);
  const [pipelineActive, setPipelineActive] = useState(false);
  const [selectedOffice, setSelectedOffice] = useState<HqSector | null>(null);
  const [now, setNow] = useState(new Date());
  const [adminFlags, setAdminFlags] = useState<AdminFlags | null>(null);
  const [adminOpen, setAdminOpen] = useState(false);
  const [agentsError, setAgentsError] = useState<string | null>(null);
  const [previewMode, setPreviewMode] = useState(false);

  useEffect(() => {
    prefetchAllOfficeRoutes(router);
  }, [router]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Enter" || !selectedOffice) return;
      const target = event.target;
      if (
        target instanceof HTMLElement &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.isContentEditable)
      ) {
        return;
      }
      navigate(selectedOffice.href);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [navigate, selectedOffice]);

  useEffect(() => {
    setPreviewMode(
      new URLSearchParams(window.location.search).get("preview") === "1"
    );
    const cached = getLobbyStatsCache();
    if (cached) setStats(cached);

    const loadSecondary = () => {
      fetchLobbyStats()
        .then(setStats)
        .catch(() => {
          const cached = getLobbyStatsCache();
          if (cached) setStats(cached);
        });

      fetchAgentsStatus()
        .then((result) => {
          setAgentsError(result.ok ? null : result.error);
          setAgents(result.data.agents);
          setRecentLogs(result.data.recentLogs);
          setActiveAgents(countActiveAgents(result.data.agents));
          setPipelineActive(result.data.pipelineActive);
        })
        .catch((err: unknown) => {
          setAgentsError(
            err instanceof Error ? err.message : "Agents indisponibles",
          );
          setAgents({});
          setRecentLogs([]);
          setActiveAgents(0);
          setPipelineActive(false);
        });

      fetchAdminFlags()
        .then(setAdminFlags)
        .catch(() => setAdminFlags(null));
    };

    const idleId =
      typeof requestIdleCallback !== "undefined"
        ? requestIdleCallback(loadSecondary, { timeout: 1500 })
        : (setTimeout(loadSecondary, 80) as unknown as number);

    const clock = setInterval(() => setNow(new Date()), 60_000);
    return () => {
      clearInterval(clock);
      if (typeof cancelIdleCallback !== "undefined") {
        cancelIdleCallback(idleId);
      } else {
        clearTimeout(idleId);
      }
    };
  }, []);

  const tierAdminLinks = ADMIN_LINKS.filter((link) =>
    isAdminPageEnabled(adminFlags, link.flag, previewMode),
  );
  const adminToolLinks = [
    ...STATIC_ADMIN_LINKS,
    ...tierAdminLinks.map((link) => ({
      ...link,
      href: withAdminPreview(link.href, previewMode),
    })),
    ...(tierAdminLinks.length > 0 || !adminFlags?.preview_allowed
      ? []
      : [{ href: withAdminPreview("/admin", true), label: "Admin (preview)" }]),
  ];

  return (
    <div className="relative h-full min-h-0 w-full flex-1 bg-obsidian">
      {(stats.refreshError || agentsError) ? (
        <div className="pointer-events-none absolute inset-x-0 top-2 z-40 flex justify-center px-4">
          <p className="pointer-events-auto max-w-xl rounded-lg border border-amber-500/30 bg-obsidian/95 px-3 py-2 text-center font-body text-xs text-amber-200 shadow-lg backdrop-blur-sm">
            {stats.refreshError ?? agentsError}
          </p>
        </div>
      ) : null}
      <div className="relative h-full min-h-0 flex-1">
        <Suspense
          fallback={
            <div className="absolute inset-0 flex items-center justify-center font-body text-xs text-titanium/50">
              Chargement carte…
            </div>
          }
        >
          <HqHubMap
            stats={stats}
            selectedOfficeId={selectedOffice?.id ?? null}
            onSelectOffice={setSelectedOffice}
          />
        </Suspense>

        <aside className="pointer-events-none absolute inset-y-0 bottom-9 left-0 z-20 hidden w-[min(17rem,22vw)] lg:block">
          <div className="pointer-events-auto h-full overflow-hidden">
            <HqActivityMonitorPanel
              stats={stats}
              agents={agents}
              activeAgents={activeAgents}
              recentLogs={recentLogs}
              pipelineActive={pipelineActive}
              selectedOffice={selectedOffice}
              onSelectOffMap={setSelectedOffice}
            />
          </div>
        </aside>

        <aside className="pointer-events-none absolute inset-y-0 bottom-9 right-0 z-20 hidden w-[min(17rem,22vw)] lg:block">
          <div className="pointer-events-auto h-full overflow-hidden">
            <HqAgentPanel
              stats={stats}
              agents={agents}
              selectedOffice={selectedOffice}
            />
          </div>
        </aside>
      </div>

      <footer className="absolute inset-x-0 bottom-0 z-50 shrink-0 border-t border-copper/10 bg-obsidian/80 backdrop-blur-md">
        <div className="flex h-9 items-center px-2 sm:px-3">
          <Link
            href="/"
            className="flex h-8 items-center gap-2 rounded px-2 transition hover:bg-white/5"
            title="ALNUA Hub"
          >
            <AlnuaLogo variant="icon" height={22} />
          </Link>

          <div className="flex flex-1 items-center justify-end gap-1 sm:gap-2">
            {activeAgents > 0 ? (
              <Link
                href="/openroom"
                className="hidden rounded px-2 py-1 font-body text-[11px] text-emerald-400 hover:bg-white/5 sm:inline"
              >
                {activeAgents} actif{activeAgents > 1 ? "s" : ""}
              </Link>
            ) : null}

            <div className="relative">
              <button
                type="button"
                onClick={() => setAdminOpen((v) => !v)}
                className="flex h-8 w-8 items-center justify-center rounded text-titanium transition hover:bg-white/5 hover:text-ivory"
                aria-label="Outils admin"
              >
                <MoreHorizontal className="h-4 w-4" />
              </button>
              {adminOpen ? (
                <>
                  <button
                    type="button"
                    className="fixed inset-0 z-40"
                    aria-label="Fermer"
                    onClick={() => setAdminOpen(false)}
                  />
                  <div className="absolute bottom-10 right-0 z-50 min-w-[10rem] rounded-lg border border-copper/20 bg-obsidian py-1 shadow-xl">
                    {adminToolLinks.map((link) => (
                      <Link
                        key={link.href}
                        href={link.href}
                        onClick={() => setAdminOpen(false)}
                        className="block px-3 py-1.5 font-body text-xs text-titanium hover:bg-copper/10 hover:text-ivory"
                      >
                        {link.label}
                      </Link>
                    ))}
                  </div>
                </>
              ) : null}
            </div>

            <Link
              href="/settings"
              className="flex h-8 w-8 items-center justify-center rounded text-titanium transition hover:bg-white/5 hover:text-ivory"
              aria-label="Paramètres"
            >
              <Settings className="h-4 w-4" />
            </Link>

            <Link
              href="/ceo"
              className="relative flex h-8 w-8 items-center justify-center rounded text-titanium transition hover:bg-white/5 hover:text-ivory"
              aria-label="Notifications CEO"
            >
              <Bell className="h-4 w-4" />
              {stats.ceoNotifications > 0 ? (
                <span className="absolute right-0.5 top-0.5 h-2 w-2 rounded-full bg-copper" />
              ) : null}
            </Link>

            <span className="mx-1 hidden h-3 w-px bg-copper/20 sm:block" />

            <div className="flex flex-col items-end px-2 py-0.5 text-right leading-tight">
              <p className="font-title text-[11px] font-medium text-ivory">
                Siège social <span className="text-copper">ALNUA</span>
              </p>
              <p className="font-body text-[10px] text-titanium/80">
                {format(now, "EEE d MMM · HH:mm", { locale: fr })}
              </p>
            </div>

            <span
              className={cn(
                "ml-1 h-2 w-2 shrink-0 rounded-full",
                !stats.apiOnline
                  ? "bg-red-500"
                  : stats.apiAuthenticated
                    ? "bg-emerald-500"
                    : "bg-amber-500",
              )}
              title={
                !stats.apiOnline
                  ? "API offline"
                  : stats.apiAuthenticated
                    ? "API connectée"
                    : "Clé API invalide"
              }
            />
          </div>
        </div>
      </footer>
    </div>
  );
}
