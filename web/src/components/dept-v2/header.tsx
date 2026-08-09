"use client";

import Link from "next/link";
import { AlnuaStar } from "@/components/brand/alnua-star";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { useConsoleData } from "@/components/console/console-provider";
import { useAgentStatuses } from "@/hooks/use-agent-statuses";
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

export interface DeptV2HeaderProps {
  /** Route canonique du département (`/app`, `/rd`…) pour l'onglet Départements. */
  deptHref: string;
}

export function DeptV2Header({ deptHref }: DeptV2HeaderProps) {
  const { stats } = useConsoleData();
  const statuses = useAgentStatuses();
  const topTabs = deptV2TopTabs(deptHref);

  return (
    <header
      className="flex h-[clamp(56px,6vh,64px)] shrink-0 items-stretch border-b"
      style={{ borderColor: C.line, background: C.obsidianDeep }}
    >
      <Link
        href={ROUTES.home}
        className="flex w-[clamp(178px,13.7vw,210px)] shrink-0 items-center gap-[11px] border-r pl-[18px]"
        style={{ borderColor: C.line }}
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
          <span
            className="block font-title text-[21px] leading-none tracking-[4px]"
            style={{ color: C.copperLight }}
          >
            ALNUA
          </span>
          <span className="mt-[3px] block text-[8px] tracking-[3.4px]" style={{ color: C.dim }}>
            AGENTIC OS
          </span>
        </span>
      </Link>

      <div className="flex flex-1 items-center justify-between gap-4 px-5">
        <div className="flex min-w-0 items-center gap-[11px]">
          <AgentAvatar agentId={HUB_CHIEF.agentId} name={HUB_CHIEF.name} size={38} ring />
          <span className="min-w-0">
            <span className="block truncate text-[12.5px] font-medium">
              {HUB_CHIEF.shortRole} : {HUB_CHIEF.name}
            </span>
            <span className="mt-[3px] flex items-center gap-2">
              <span
                className="flex items-center gap-1 rounded-[10px] border px-[7px] py-px"
                style={{ borderColor: "rgba(127,201,140,.28)" }}
              >
                <span className="h-[5px] w-[5px] rounded-full" style={{ background: C.online }} />
                <span className="text-[9px]" style={{ color: C.onlineSoft }}>
                  {STATUS_TEXT[statuses[HUB_CHIEF.agentId]?.status ?? "idle"]}
                </span>
              </span>
            </span>
          </span>
        </div>

        <nav className="hidden items-center gap-1 lg:flex">
          {topTabs.map((t) => (
            <Link
              key={t.label}
              href={t.href}
              className={cn(
                "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[12px] transition-colors",
                t.active ? "border" : "border border-transparent hover:opacity-90",
              )}
              style={
                t.active
                  ? {
                      borderColor: C.copperLine,
                      background: C.copperFillActive,
                      color: C.copperLight,
                    }
                  : { color: C.warm }
              }
            >
              <span className="text-[12px] opacity-90">{t.icon}</span>
              <span className="hidden xl:inline">{t.label}</span>
            </Link>
          ))}
        </nav>

        <div className="flex shrink-0 items-center gap-[18px]">
          <span
            className="relative flex h-[34px] w-[34px] items-center justify-center rounded-full border text-[13px]"
            style={{ borderColor: C.line }}
          >
            🔔
            {stats.ceoNotifications > 0 ? (
              <span
                className="absolute right-[3px] top-[2px] h-[6px] w-[6px] rounded-full"
                style={{ background: C.copper, boxShadow: `0 0 6px ${copperAlpha(0.5)}` }}
              />
            ) : null}
          </span>
          <span className="flex items-center gap-[9px]">
            <AgentAvatar agentId={HUB_OWNER.id} name={HUB_OWNER.name} size={36} />
            <span className="hidden xl:block">
              <span className="block text-[12px] font-medium">{HUB_OWNER.name}</span>
              <span className="block text-[9.5px]" style={{ color: C.dim }}>
                {HUB_OWNER.role}
              </span>
            </span>
            <span className="text-[9px]" style={{ color: C.dim }}>
              ▾
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
  return (
    <div
      className={cn(
        "alnua-scroll flex h-full w-full flex-col overflow-x-auto overflow-y-auto",
        className,
      )}
      style={{ background: C.obsidian, color: C.ivory }}
    >
      <DeptV2Header deptHref={deptHref} />
      <div className="flex min-h-[600px] flex-1">
        <DeptV2Sidebar activeDeptId={activeDeptId} coreSubtitle={coreSubtitle} />
        {children}
      </div>
    </div>
  );
}
