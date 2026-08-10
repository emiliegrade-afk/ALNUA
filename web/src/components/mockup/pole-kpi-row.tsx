"use client";

import { motion } from "framer-motion";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { MiniTrend } from "./views/finances-charts";
import { poleFadeUp } from "./pole-page-shell";

export interface PoleKpi {
  label: string;
  value: string;
  delta: string;
  deltaType: "up" | "down" | "neutral";
  trend: number[];
  color: string;
  onClick?: () => void;
}

export function PoleKpiRow({ kpis }: { kpis: PoleKpi[] }) {
  return (
    <div
      className={cn(
        "grid gap-2",
        kpis.length <= 4 && "grid-cols-2 sm:grid-cols-4",
        kpis.length === 5 && "grid-cols-2 sm:grid-cols-3 lg:grid-cols-5",
        kpis.length >= 6 && "grid-cols-2 sm:grid-cols-3 lg:grid-cols-6",
      )}
    >
      {kpis.map((k, i) => {
        const clickable = Boolean(k.onClick);
        const Tag = clickable ? "button" : "div";
        return (
          <motion.div key={k.label} custom={i} variants={poleFadeUp} initial="hidden" animate="show">
            <Tag
              type={clickable ? "button" : undefined}
              onClick={k.onClick}
              className={cn(
                "w-full rounded-xl border border-bronze-faint bg-obsidian/60 p-3 text-left transition-all duration-300",
                clickable &&
                  "cursor-pointer hover:-translate-y-0.5 hover:border-copper/40 hover:shadow-[0_0_20px_rgba(224,155,106,0.12)] active:scale-[0.98]",
              )}
            >
              <p className="text-[9px] uppercase tracking-[0.16em] text-titane/50">{k.label}</p>
              <p className="mt-1 font-title text-lg font-semibold text-ivoire">{k.value}</p>
              <div className="mt-0.5 flex items-center gap-1 text-[10px]">
                {k.deltaType === "up" ? (
                  <ArrowUpRight className="h-3 w-3 text-online" />
                ) : k.deltaType === "down" ? (
                  <ArrowDownRight className="h-3 w-3 text-orange-400" />
                ) : null}
                <span
                  className={cn(
                    k.deltaType === "up" && "text-online",
                    k.deltaType === "down" && "text-orange-400",
                    k.deltaType === "neutral" && "text-titane/55",
                  )}
                >
                  {k.delta}
                </span>
                <span className="text-titane/40">vs 30j</span>
              </div>
              <div className="mt-2">
                <MiniTrend values={k.trend} color={k.color} />
              </div>
            </Tag>
          </motion.div>
        );
      })}
    </div>
  );
}

export function SeeAllLink({
  onClick,
  label,
}: {
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="text-[10px] text-copper transition-colors hover:text-copper-light hover:underline"
    >
      {label} →
    </button>
  );
}
