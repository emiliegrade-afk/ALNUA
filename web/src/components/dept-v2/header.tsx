"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Bell } from "lucide-react";
import { AlnuaStar } from "@/components/brand/alnua-star";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { useConsoleData } from "@/components/console/console-provider";
import { useAgentStatuses } from "@/hooks/use-agent-statuses";
import { useHubHealthLive } from "@/hooks/use-hub-health-live";
import { HUB_CHIEF, HUB_OWNER } from "@/lib/console/owner";
import { ROUTES } from "@/lib/routes";
import { cn } from "@/lib/utils";
import {
  ALNUA_STAR_GLOW_RGB,
  ALNUA_STAR_SPARK_MID,
  ALNUA_STAR_SPARK_OUTER,
  C,
  copperAlpha,
  STATUS_TEXT,
} from "@/app/app-v2/shared";
import { deptV2TopTabs } from "./nav";
import { DeptV2Sidebar } from "./sidebar";

const SIDEBAR_KEY = "alnua.dept-sidebar-collapsed";

export interface DeptV2HeaderProps {
  /** Route canonique du département (`/app`, `/rd`…) pour l'onglet Départements. */
  deptHref: string;
  /** Onglet actif — Command Center = `overview`. */
  activeTab?: "overview" | "dept" | "missions" | "analytics" | "resources";
  /** Menu mobile (sidebar). */
  onMobileMenu?: () => void;
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

export function DeptV2Header({
  deptHref,
  activeTab = "dept",
  onMobileMenu,
}: DeptV2HeaderProps) {
  const { stats } = useConsoleData();
  const statuses = useAgentStatuses();
  const { phase } = useHubHealthLive();
  const now = useLiveClock();
  const topTabs = deptV2TopTabs(deptHref, activeTab);

  const hubOk = phase === "ok";
  const hubLabel =
    phase === "ok"
      ? "Hub connecté"
      : phase === "checking"
        ? "Sync…"
        : phase === "key"
          ? "Clé API requise"
          : "Hub hors ligne";
  const clock =
    now?.toLocaleTimeString("fr-FR", { hour12: false }) ?? "--:--:--";

  return (
    <header
      className="flex h-[clamp(56px,6vh,64px)] shrink-0 items-stretch border-b bg-void"
      style={{ borderColor: "rgba(184,189,196,0.16)" }}
    >
      <Link
        href={ROUTES.home}
        className="flex w-[clamp(178px,13.7vw,210px)] shrink-0 items-center gap-[11px] border-r bg-void pl-[18px]"
        style={{ borderColor: "rgba(184,189,196,0.16)" }}
      >
        <span
          className="flex h-[38px] w-[38px] shrink-0 items-center justify-center rounded-full border"
          style={{
            borderColor: C.copperLine,
            background: `radial-gradient(circle, ${copperAlpha(0.14)}, transparent 70%)`,
            boxShadow: `0 0 14px ${copperAlpha(0.18)}`,
          }}
        >
          <AlnuaStar
            size={24}
            animated={false}
            sparkMid={ALNUA_STAR_SPARK_MID}
            sparkOuter={ALNUA_STAR_SPARK_OUTER}
            glowColorRgb={ALNUA_STAR_GLOW_RGB}
          />
        </span>
        <span>
          <span className="block font-title text-[21px] leading-none tracking-[4px] text-metal-copper">
            ALNUA
          </span>
          <span className="mt-[3px] block text-[8px] tracking-[3.4px]" style={{ color: C.dim }}>
            AGENTIC OS
          </span>
        </span>
      </Link>

      <div className="flex flex-1 items-center justify-between gap-3 px-4 sm:px-5">
        <div className="flex min-w-0 items-center gap-[11px]">
          {onMobileMenu ? (
            <button
              type="button"
              onClick={onMobileMenu}
              className="-ml-1 p-2 text-metal-titanium hover:text-ivoire lg:hidden"
              aria-label="Ouvrir le menu"
            >
              <span className="text-xl leading-none">≡</span>
            </button>
          ) : null}
          <AgentAvatar agentId={HUB_CHIEF.agentId} name={HUB_CHIEF.name} size={38} ring />
          <span className="min-w-0">
            <span className="block truncate text-[12.5px] font-medium">
              {HUB_CHIEF.shortRole} : {HUB_CHIEF.name}
            </span>
            <span className="mt-[3px] flex items-center gap-2">
              <span
                className="flex items-center gap-1 rounded-[10px] border px-[7px] py-px"
                style={{ borderColor: "rgba(45,212,191,.28)" }}
              >
                <span className="h-[5px] w-[5px] rounded-full" style={{ background: C.online }} />
                <span className="text-[9px]" style={{ color: C.onlineSoft }}>
                  {STATUS_TEXT[statuses[HUB_CHIEF.agentId]?.status ?? "idle"]}
                </span>
              </span>
            </span>
          </span>
        </div>

        <nav
          className="hidden items-center gap-0.5 lg:flex"
          aria-label="Navigation principale"
        >
          {topTabs.map((t) => (
            <Link
              key={t.label}
              href={t.href}
              className={cn(
                "px-3 py-1.5 text-[12px] tracking-wide transition-colors",
                t.active
                  ? "border border-copper/50 text-metal-copper shadow-[0_0_14px_rgba(224,155,106,0.25)]"
                  : "border border-transparent text-titanium hover:text-ivoire",
              )}
            >
              {t.label}
            </Link>
          ))}
        </nav>

        <div className="flex shrink-0 items-center gap-3 sm:gap-4">
          <div
            className={cn(
              "hidden items-center gap-2 border px-2.5 py-1 sm:flex",
              hubOk ? "border-teal/30 bg-teal/5" : "border-danger/40 bg-danger/5",
            )}
            title={hubLabel}
          >
            <span
              className={cn(
                "h-2 w-2 rounded-full",
                hubOk ? "animate-pulse bg-teal" : "bg-danger",
              )}
            />
            <span
              className={cn(
                "text-[11px] font-medium tabular-nums",
                hubOk ? "text-teal" : "text-danger",
              )}
              suppressHydrationWarning
            >
              {hubLabel}
              {hubOk ? ` · ${clock}` : null}
            </span>
          </div>

          <button
            type="button"
            className="relative flex h-[34px] w-[34px] items-center justify-center border text-metal-titanium transition-colors hover:text-copper-light"
            style={{ borderColor: C.line }}
            aria-label={
              stats.ceoNotifications > 0
                ? `Notifications — ${stats.ceoNotifications} en attente`
                : "Notifications"
            }
            title="Notifications"
          >
            <Bell className="h-4 w-4" strokeWidth={1.6} />
            {stats.ceoNotifications > 0 ? (
              <span
                className="absolute right-[3px] top-[2px] h-[6px] w-[6px] rounded-full"
                style={{
                  background: C.copper,
                  boxShadow: `0 0 6px ${copperAlpha(0.5)}`,
                }}
              />
            ) : null}
          </button>

          <span
            className="flex items-center gap-[9px]"
            title={`${HUB_OWNER.name} — ${HUB_OWNER.role}`}
          >
            <AgentAvatar agentId={HUB_OWNER.id} name={HUB_OWNER.name} size={36} />
            <span className="hidden xl:block">
              <span className="block text-[12px] font-medium">{HUB_OWNER.name}</span>
              <span className="block text-[9.5px]" style={{ color: C.dim }}>
                {HUB_OWNER.role}
              </span>
            </span>
          </span>
        </div>
      </div>
    </header>
  );
}

export function DeptV2PageShell({
  deptHref,
  activeDeptId,
  coreSubtitle,
  children,
  className,
}: {
  deptHref: string;
  activeDeptId: string;
  coreSubtitle?: string;
  children: React.ReactNode;
  className?: string;
}) {
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    try {
      setCollapsed(localStorage.getItem(SIDEBAR_KEY) === "1");
    } catch {
      /* ignore */
    }
  }, []);

  function handleCollapsedChange(next: boolean) {
    setCollapsed(next);
    try {
      localStorage.setItem(SIDEBAR_KEY, next ? "1" : "0");
    } catch {
      /* ignore */
    }
  }

  return (
    <div
      className={cn(
        "dept-void-shell alnua-scroll flex h-full w-full flex-col overflow-x-auto overflow-y-auto",
        className,
      )}
      style={{ background: C.void, color: C.ivory }}
    >
      <DeptV2Header deptHref={deptHref} />
      <div className="flex min-h-[600px] flex-1">
        <DeptV2Sidebar
          activeDeptId={activeDeptId}
          coreSubtitle={coreSubtitle}
          collapsed={collapsed}
          onCollapsedChange={handleCollapsedChange}
        />
        {children}
      </div>
    </div>
  );
}
