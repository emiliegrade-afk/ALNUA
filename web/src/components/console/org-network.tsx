"use client";

import { motion } from "framer-motion";
import { useConsoleData } from "./console-provider";
import { AlnuaLogo } from "./alnua-logo";
import { cn } from "@/lib/utils";

interface OrgNetworkProps {
  onSelect: (id: string) => void;
  activeId?: string | null;
}

/**
 * Radial org map: ALNUA core at center, 11 pôles arranged around it.
 * Pure SVG + HTML overlay, fully responsive.
 */
export function OrgNetwork({ onSelect, activeId }: OrgNetworkProps) {
  const { departments } = useConsoleData();
  const count = departments.length;
  const radius = 42; // % of half the box

  return (
    <div className="relative h-full w-full min-h-0 flex items-center justify-center">
      <div className="relative h-full max-h-full aspect-square w-auto max-w-full mx-auto">
      {/* SVG connectors */}
      <svg
        viewBox="0 0 100 100"
        className="absolute inset-0 w-full h-full"
        fill="none"
        preserveAspectRatio="xMidYMid meet"
      >
        {departments.map((d, i) => {
          const angle = (i / count) * Math.PI * 2 - Math.PI / 2;
          const x = 50 + radius * Math.cos(angle);
          const y = 50 + radius * Math.sin(angle);
          const isActive = activeId === d.id;
          return (
            <line
              key={d.id}
              x1="50"
              y1="50"
              x2={x}
              y2={y}
              stroke={isActive ? d.glow : "#C08A72"}
              strokeOpacity={isActive ? 0.6 : 0.18}
              strokeWidth={isActive ? 0.6 : 0.3}
              strokeDasharray="0.6 1.2"
              className="transition-all duration-300"
            />
          );
        })}
        {/* concentric rings */}
        <circle cx="50" cy="50" r="20" stroke="#C08A72" strokeOpacity="0.12" strokeWidth="0.2" />
        <circle cx="50" cy="50" r="32" stroke="#C08A72" strokeOpacity="0.08" strokeWidth="0.2" strokeDasharray="0.5 1" />
        <circle cx="50" cy="50" r="42" stroke="#C08A72" strokeOpacity="0.06" strokeWidth="0.2" />
      </svg>

      {/* Center core */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10">
        <motion.div
          initial={{ opacity: 0, scale: 0.6 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="relative flex flex-col items-center"
        >
          <div className="absolute inset-0 -m-6 rounded-full bg-bronze/10 blur-2xl animate-alnua-pulse" />
          <div className="relative flex flex-col items-center">
            <AlnuaLogo variant="icon" size={44} staticMark />
          </div>
          <span className="mt-2 text-[10px] tracking-[0.3em] text-bronze uppercase">
            Core
          </span>
        </motion.div>
      </div>

      {/* Department nodes */}
      {departments.map((d, i) => {
        const angle = (i / count) * Math.PI * 2 - Math.PI / 2;
        const x = 50 + radius * Math.cos(angle);
        const y = 50 + radius * Math.sin(angle);
        const Icon = d.icon;
        const isActive = activeId === d.id;
        return (
          <button
            key={d.id}
            type="button"
            onClick={() => onSelect(d.id)}
            className="absolute z-20 -translate-x-1/2 -translate-y-1/2 group focus:outline-none"
            style={{ left: `${x}%`, top: `${y}%` }}
            aria-label={d.name}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.4 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.45, delay: 0.2 + i * 0.04 }}
              whileHover={{ scale: 1.18 }}
              className={cn(
                "relative flex h-11 w-11 sm:h-14 sm:w-14 items-center justify-center rounded-xl border bg-obsidian-deep transition-all",
                isActive
                  ? "border-bronze shadow-glow"
                  : "border-bronze-faint group-hover:border-bronze/60"
              )}
              style={{ boxShadow: isActive ? `0 0 20px -4px ${d.glow}` : undefined }}
            >
              <Icon className={cn("h-4 w-4 sm:h-5 sm:w-5", d.accent)} />
              {/* status dot */}
              <span className="absolute -top-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-bronze-bright border-2 border-obsidian-deep animate-alnua-pulse" />
            </motion.div>
            {/* label */}
            <span className="absolute top-full mt-1.5 left-1/2 -translate-x-1/2 whitespace-nowrap text-[9px] sm:text-[10px] font-medium text-titane/70 group-hover:text-bronze-bright transition-colors">
              {d.name.replace("Bureau ", "").replace("Pôle ", "")}
            </span>
          </button>
        );
      })}
      </div>
    </div>
  );
}
