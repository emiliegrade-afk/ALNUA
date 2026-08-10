"use client";

import Link from "next/link";
import { ChevronLeft, ChevronRight, PanelLeftClose, PanelLeft } from "lucide-react";
import { AlnuaStar } from "@/components/brand/alnua-star";
import { useConsoleData } from "@/components/console/console-provider";
import { CONSOLE_POLES } from "@/lib/console/departments";
import {
  ALNUA_STAR_GLOW_RGB,
  ALNUA_STAR_SPARK_MID,
  ALNUA_STAR_SPARK_OUTER,
  C,
  copperAlpha,
} from "@/app/app-v2/shared";
import {
  DEPT_V2_DASHBOARD_NAV,
  DEPT_V2_ICONS,
  DEPT_V2_TOOLS_NAV,
} from "./nav";
import { DeptV2SectionBox } from "./section-box";

export interface DeptV2SidebarProps {
  activeDeptId: string;
  coreSubtitle?: string;
  /** Colonne rabattue — rail icônes uniquement. */
  collapsed?: boolean;
  onCollapsedChange?: (collapsed: boolean) => void;
}

/** Sidebar Jarvis — noir void ; collapsible pour gagner l'espace métier. */
export function DeptV2Sidebar({
  activeDeptId,
  coreSubtitle = "Système opérationnel",
  collapsed = false,
  onCollapsedChange,
}: DeptV2SidebarProps) {
  const { stats } = useConsoleData();
  const poles = CONSOLE_POLES.filter((pole) => pole.id !== "ceo");

  if (collapsed) {
    return (
      <aside
        className="flex w-12 shrink-0 flex-col items-center gap-2 overflow-y-auto border-r bg-void py-3 transition-[width] duration-300 ease-out"
        style={{ borderColor: "rgba(167,173,181,0.16)" }}
      >
        <button
          type="button"
          onClick={() => onCollapsedChange?.(false)}
          className="flex h-8 w-8 items-center justify-center text-titanium transition-colors hover:text-copper-light"
          title="Ouvrir les départements"
          aria-label="Ouvrir la colonne départements"
        >
          <PanelLeft className="h-4 w-4" />
        </button>
        <div className="my-1 h-px w-6 bg-titanium/20" />
        {poles.map((pole) => {
          const active = pole.id === activeDeptId;
          const icon = DEPT_V2_ICONS[pole.id] ?? "◈";
          const label = pole.name.replace("Bureau ", "").replace("Pôle ", "");
          return (
            <Link
              key={pole.id}
              href={pole.href}
              title={label}
              className="flex h-8 w-8 items-center justify-center text-[12px] transition-colors hover:bg-white/[0.04]"
              style={{
                color: active ? C.copperLight : C.titaniumMuted,
                boxShadow: active ? `inset 2px 0 0 ${C.copper}` : undefined,
                background: active ? "rgba(224,155,106,0.08)" : undefined,
              }}
            >
              {icon}
            </Link>
          );
        })}
        <button
          type="button"
          onClick={() => onCollapsedChange?.(false)}
          className="mt-auto flex h-8 w-8 items-center justify-center text-titanium/60 hover:text-copper-light"
          title="Déplier"
          aria-label="Déplier la colonne"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </aside>
    );
  }

  return (
    <aside
      className="flex w-[clamp(178px,13.7vw,210px)] shrink-0 flex-col gap-3 overflow-y-auto border-r bg-void px-3 py-4 transition-[width] duration-300 ease-out"
      style={{ borderColor: "rgba(167,173,181,0.16)" }}
    >
      <div className="mb-0.5 flex items-center justify-between px-1">
        <span className="text-[8px] font-medium uppercase tracking-[0.2em] text-titanium/50">
          Navigation
        </span>
        <button
          type="button"
          onClick={() => onCollapsedChange?.(true)}
          className="flex h-7 w-7 items-center justify-center text-titanium/70 transition-colors hover:text-copper-light"
          title="Rabattre la colonne"
          aria-label="Rabattre la colonne départements"
        >
          <PanelLeftClose className="h-3.5 w-3.5" />
        </button>
      </div>

      <DeptV2SectionBox title="TABLEAU DE BORD">
        {DEPT_V2_DASHBOARD_NAV.map((it) => (
          <Link
            key={it.label}
            href={it.href}
            className="flex items-center justify-between gap-1 whitespace-nowrap px-2 py-[7px] text-[12px] transition-colors hover:bg-white/[0.03]"
            style={{ color: C.titanium }}
          >
            <span className="flex min-w-0 items-center gap-2">
              <span
                className="w-[15px] shrink-0 text-center text-[12px]"
                style={{ color: C.copperLight }}
              >
                {it.icon}
              </span>
              {it.label}
            </span>
            {"badge" in it && it.badge && stats.ceoNotifications > 0 ? (
              <span
                className="border px-1.5 text-[9px]"
                style={{ borderColor: C.copperLine, color: C.copperLight }}
              >
                {stats.ceoNotifications}
              </span>
            ) : null}
          </Link>
        ))}
      </DeptV2SectionBox>

      <DeptV2SectionBox title="DÉPARTEMENTS">
        {poles.map((pole, i) => {
          const active = pole.id === activeDeptId;
          const icon = DEPT_V2_ICONS[pole.id] ?? "◈";
          const label = pole.name.replace("Bureau ", "").replace("Pôle ", "");
          return (
            <Link
              key={pole.id}
              href={pole.href}
              className="flex items-center justify-between px-2 py-[7px] transition-colors hover:bg-white/[0.03]"
              style={
                active
                  ? {
                      background: "rgba(224,155,106,0.08)",
                      color: C.copperLight,
                      boxShadow: `inset 2px 0 0 ${C.copper}, 0 0 18px ${copperAlpha(0.12)}`,
                    }
                  : { color: C.titanium }
              }
            >
              <span className="flex min-w-0 items-center gap-2">
                <span
                  className="w-[16px] shrink-0 text-center text-[11px]"
                  style={{ color: active ? C.copperLight : C.titaniumMuted }}
                >
                  {icon}
                </span>
                <span
                  className="text-[10.5px] tabular-nums"
                  style={{ color: active ? C.copperDim : C.titaniumDim }}
                >
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span
                  className={
                    active
                      ? "truncate text-[12px] text-metal-copper"
                      : "truncate text-[12px]"
                  }
                >
                  {label}
                </span>
              </span>
              <span
                className="text-[10px]"
                style={{ color: active ? C.copper : C.titaniumDim }}
              >
                ›
              </span>
            </Link>
          );
        })}
      </DeptV2SectionBox>

      <DeptV2SectionBox title="OUTILS">
        {DEPT_V2_TOOLS_NAV.map((t) => (
          <Link
            key={t.label}
            href={t.href}
            className="flex items-center justify-between gap-1 whitespace-nowrap px-2 py-[7px] text-[12px] transition-colors hover:bg-white/[0.03]"
            style={{ color: C.titanium }}
          >
            <span className="flex min-w-0 items-center gap-2">
              <span
                className="w-[15px] shrink-0 text-center text-[11px]"
                style={{ color: C.copperLight }}
              >
                {t.icon}
              </span>
              {t.label}
            </span>
            <span className="text-[10px]" style={{ color: C.titaniumDim }}>
              ›
            </span>
          </Link>
        ))}
      </DeptV2SectionBox>

      <div
        className="relative mt-auto overflow-hidden border border-titanium/15 bg-void p-3"
        style={{
          borderColor: "rgba(167,173,181,0.16)",
          boxShadow: `inset 0 0 40px ${copperAlpha(0.06)}`,
        }}
      >
        <div className="flex items-center justify-center gap-2">
          <span
            className="h-px w-4"
            style={{
              background: `linear-gradient(90deg,transparent,${copperAlpha(0.45)})`,
            }}
          />
          <span className="text-[10px] tracking-[0.24em] text-metal-copper">
            ALNUA CORE
          </span>
          <span
            className="h-px w-4"
            style={{
              background: `linear-gradient(90deg,${copperAlpha(0.45)},transparent)`,
            }}
          />
        </div>
        <p
          className="mt-[3px] text-center text-[9.5px]"
          style={{ color: C.titaniumDim }}
        >
          {coreSubtitle}
        </p>
        <div className="relative mt-1.5 flex h-[100px] items-center justify-center">
          <svg
            viewBox="0 0 168 112"
            className="absolute inset-0 m-auto h-full w-full opacity-35"
            aria-hidden
          >
            <g fill="none" stroke={copperAlpha(0.28)}>
              <ellipse cx="84" cy="56" rx="78" ry="30" />
              <ellipse
                cx="84"
                cy="56"
                rx="60"
                ry="46"
                stroke={copperAlpha(0.14)}
              />
              <ellipse cx="84" cy="56" rx="44" ry="17" />
            </g>
          </svg>
          <AlnuaStar
            size={48}
            glow
            className="relative"
            sparkMid={ALNUA_STAR_SPARK_MID}
            sparkOuter={ALNUA_STAR_SPARK_OUTER}
            glowColorRgb={ALNUA_STAR_GLOW_RGB}
          />
        </div>
        <div className="mt-0.5 flex items-center justify-center gap-2">
          <span
            className="h-[6px] w-[6px] shrink-0 rounded-full"
            style={{ background: C.online, boxShadow: `0 0 8px ${C.online}` }}
          />
          <p
            className="text-left text-[9.5px] leading-tight"
            style={{ color: C.titaniumDim }}
          >
            Tous les systèmes
            <br />
            opérationnels
          </p>
        </div>
      </div>

      <button
        type="button"
        onClick={() => onCollapsedChange?.(true)}
        className="flex items-center justify-center gap-1.5 border border-titanium/15 py-1.5 text-[9px] uppercase tracking-[0.16em] text-titanium/60 transition-colors hover:border-copper/35 hover:text-copper-light"
      >
        <ChevronLeft className="h-3 w-3" />
        Rabattre
      </button>
    </aside>
  );
}
