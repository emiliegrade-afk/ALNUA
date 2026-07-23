"use client";

import Image from "next/image";
import { DEPT_COLORS, type DeptKey } from "@/lib/dept-colors";
import type { AgentStatusKind } from "@/lib/openroom-api";
import { getAgentLoopSrc, getAgentOfficeAssets, hasActTwoLoops } from "@/lib/agent-assets";
import { cn } from "@/lib/utils";

interface AgentOfficeAvatarProps {
  agentId: string;
  name: string;
  role: string;
  status: AgentStatusKind;
  branch: DeptKey;
  currentTask?: string;
  onClick?: () => void;
  className?: string;
  /** large = bureau hero, tile = openroom grid, compact = focus panel */
  variant?: "large" | "tile" | "compact";
}

const STATUS_RING: Record<
  AgentStatusKind,
  { ring: string; pulse?: boolean; blink?: boolean }
> = {
  idle: { ring: "border-titanium/20" },
  working: { ring: "border-copper", pulse: true },
  waiting: { ring: "border-titanium", blink: true },
  error: { ring: "border-red-500" },
};

export function AgentOfficeAvatar({
  agentId,
  name,
  role,
  status,
  branch,
  currentTask,
  onClick,
  className,
  variant = "tile",
}: AgentOfficeAvatarProps) {
  const assets = getAgentOfficeAssets(agentId);
  if (!assets) return null;

  const loopSrc = getAgentLoopSrc(agentId, status);
  const actTwoReady = hasActTwoLoops(agentId);
  const colors = DEPT_COLORS[branch];
  const ring = STATUS_RING[status];
  const isIdle = status === "idle";
  const isTile = variant === "tile";
  const isLarge = variant === "large";

  const frame = (
    <div
      className={cn(
        "relative overflow-hidden rounded-2xl border-2 bg-obsidian-2 shadow-[0_16px_48px_rgba(0,0,0,0.35)] transition-opacity duration-300",
        ring.ring,
        isTile ? "aspect-[9/16] w-full" : isLarge ? "aspect-[9/16] w-full max-w-sm" : "aspect-[9/16] w-full",
        isIdle && "opacity-50 grayscale-[20%]",
        className,
      )}
      style={{ borderColor: isIdle ? undefined : colors.border }}
    >
      {ring.pulse ? (
        <div className="pointer-events-none absolute inset-0 z-20 animate-ping rounded-2xl border-2 border-copper opacity-25" />
      ) : null}
      {ring.blink ? (
        <div className="pointer-events-none absolute inset-0 z-20 animate-pulse rounded-2xl border-2 border-titanium/60" />
      ) : null}

      {/* Poster frame — visible until video loads */}
      <Image
        src={assets.portrait}
        alt={`${name} — ${role}`}
        fill
        priority={isLarge}
        className="object-cover object-center"
        sizes={isLarge ? "(max-width: 768px) 100vw, 384px" : "(max-width: 640px) 50vw, 240px"}
      />

      {loopSrc ? (
        <video
          key={`${agentId}-${status}-${loopSrc}`}
          src={loopSrc}
          autoPlay
          loop
          muted
          playsInline
          className="absolute inset-0 z-10 h-full w-full object-cover object-center"
        />
      ) : !actTwoReady && variant !== "tile" ? (
        <div className="absolute bottom-14 left-3 right-3 z-30 rounded-lg border border-copper/20 bg-obsidian/80 px-2 py-1.5 text-center text-[10px] leading-snug text-titanium/80">
          Animation Act-Two requise — portrait statique en attendant
        </div>
      ) : null}

      <div className="pointer-events-none absolute inset-0 z-20 bg-gradient-to-t from-[#111111]/85 via-transparent to-[#111111]/10" />

      {status === "error" ? (
        <span className="absolute right-2 top-2 z-30 text-base" aria-hidden>
          ⚠️
        </span>
      ) : null}

      {!isTile ? (
        <div className="absolute bottom-0 left-0 right-0 z-30 p-4">
          <p className="font-title text-lg text-ivory">{name}</p>
          <p className="text-xs" style={{ color: colors.main }}>
            {role}
          </p>
        </div>
      ) : null}
    </div>
  );

  if (isTile) {
    return (
      <button
        type="button"
        onClick={onClick}
        className={cn(
          "relative flex w-full flex-col items-center gap-3 border-0 bg-transparent pt-10",
          onClick && "cursor-pointer hover:opacity-95",
        )}
      >
        {currentTask && status !== "idle" ? (
          <div className="absolute -top-1 left-1/2 z-10 w-44 -translate-x-1/2 rounded-lg border border-copper/20 bg-obsidian-2 px-3 py-2 text-center text-[10px] leading-snug text-titanium">
            {currentTask}
          </div>
        ) : null}
        {frame}
        <div className="text-center">
          <p className="font-title text-sm font-medium text-ivory">{name}</p>
          <p className="font-body text-[11px]" style={{ color: colors.main }}>
            {role}
          </p>
        </div>
      </button>
    );
  }

  return frame;
}
