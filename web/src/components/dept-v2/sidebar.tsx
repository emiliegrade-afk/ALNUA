"use client";

import Link from "next/link";
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
  /** Id pôle actif (`app`, `rd`, `gaming`…) — surligne la ligne DÉPARTEMENTS. */
  activeDeptId: string;
  /** Sous-titre widget ALNUA CORE (défaut : Système opérationnel). */
  coreSubtitle?: string;
}

export function DeptV2Sidebar({ activeDeptId, coreSubtitle = "Système opérationnel" }: DeptV2SidebarProps) {
  const { stats } = useConsoleData();
  const poles = CONSOLE_POLES.filter((pole) => pole.id !== "ceo");

  return (
    <aside
      className="flex w-[clamp(178px,13.7vw,210px)] shrink-0 flex-col gap-3 overflow-y-auto border-r px-3 py-4"
      style={{ borderColor: C.line, background: C.obsidianDeep }}
    >
      <DeptV2SectionBox title="TABLEAU DE BORD">
        {DEPT_V2_DASHBOARD_NAV.map((it) => (
          <Link
            key={it.label}
            href={it.href}
            className="flex items-center justify-between gap-1 whitespace-nowrap rounded-[7px] px-2 py-[7px] text-[12px] transition-colors hover:bg-obsidian-2/80"
            style={{ color: C.warm }}
          >
            <span className="flex min-w-0 items-center gap-2">
              <span className="w-[15px] shrink-0 text-center text-[12px]" style={{ color: C.copperLight }}>
                {it.icon}
              </span>
              {it.label}
            </span>
            {"badge" in it && it.badge && stats.ceoNotifications > 0 ? (
              <span
                className="rounded-lg border px-1.5 text-[9px]"
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
              className="flex items-center justify-between rounded-[7px] px-2 py-[7px] transition-colors hover:bg-obsidian-2/80"
              style={
                active
                  ? {
                      background: C.copperFillActive,
                      color: C.copperLight,
                      boxShadow: `inset 2px 0 0 ${C.copper}`,
                    }
                  : { color: C.warm }
              }
            >
              <span className="flex min-w-0 items-center gap-2">
                <span className="w-[16px] shrink-0 text-center text-[11px]" style={{ color: C.copperLight }}>
                  {icon}
                </span>
                <span className="text-[10.5px]" style={{ color: C.faint }}>
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span className="truncate text-[12px]">{label}</span>
              </span>
              <span className="text-[10px]" style={{ color: C.titaniumDim }}>
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
            className="flex items-center justify-between gap-1 whitespace-nowrap rounded-[7px] px-2 py-[7px] text-[12px] transition-colors hover:bg-obsidian-2/80"
            style={{ color: C.warm }}
          >
            <span className="flex min-w-0 items-center gap-2">
              <span className="w-[15px] shrink-0 text-center text-[11px]" style={{ color: C.copperLight }}>
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
        className="relative mt-auto overflow-hidden rounded-xl border p-3 pb-3.5"
        style={{
          borderColor: C.line,
          background: `radial-gradient(120% 90% at 50% 45%, ${copperAlpha(0.06)}, ${C.obsidian2} 72%)`,
        }}
      >
        <div className="flex items-center justify-center gap-2">
          <span
            className="h-px w-4"
            style={{ background: `linear-gradient(90deg,transparent,${copperAlpha(0.35)})` }}
          />
          <span className="text-[10px] tracking-[2.4px]" style={{ color: C.copperLight }}>
            ALNUA CORE
          </span>
          <span
            className="h-px w-4"
            style={{ background: `linear-gradient(90deg,${copperAlpha(0.35)},transparent)` }}
          />
        </div>
        <p className="mt-[3px] text-center text-[9.5px]" style={{ color: C.dim }}>
          {coreSubtitle}
        </p>
        <div className="relative mt-1.5 flex h-[100px] items-center justify-center">
          <svg viewBox="0 0 168 112" className="absolute inset-0 m-auto h-full w-full opacity-40" aria-hidden>
            <g fill="none" stroke={copperAlpha(0.2)}>
              <ellipse cx="84" cy="56" rx="78" ry="30" />
              <ellipse cx="84" cy="56" rx="60" ry="46" stroke={copperAlpha(0.12)} />
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
            className="h-[7px] w-[7px] shrink-0 rounded-full"
            style={{ background: C.online, boxShadow: `0 0 7px ${C.online}` }}
          />
          <p className="text-left text-[9.5px] leading-tight" style={{ color: C.dim }}>
            Tous les systèmes
            <br />
            opérationnels
          </p>
        </div>
      </div>
    </aside>
  );
}
