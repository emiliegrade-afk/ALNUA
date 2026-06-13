"use client";

import { DEPT_COLORS, type DeptKey } from "@/lib/dept-colors";
import type { AgentStatusKind } from "@/lib/openroom-api";
import { cn } from "@/lib/utils";

export interface AgentAvatarProps {
  name: string;
  role: string;
  emoji: string;
  status: AgentStatusKind;
  currentTask?: string;
  branch: DeptKey;
  onClick?: () => void;
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

export function AgentAvatar({
  name,
  role,
  emoji,
  status,
  currentTask,
  branch,
  onClick,
}: AgentAvatarProps) {
  const colors = DEPT_COLORS[branch];
  const ring = STATUS_RING[status];
  const isIdle = status === "idle";

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "relative flex w-full flex-col items-center gap-3 border-0 bg-transparent pt-10 transition-opacity duration-300",
        onClick && "cursor-pointer hover:opacity-90",
        isIdle && "opacity-50",
      )}
    >
      {currentTask && status !== "idle" ? (
        <div className="absolute -top-1 left-1/2 z-10 w-40 -translate-x-1/2 rounded-lg border border-copper/20 bg-obsidian-2 px-3 py-2 text-center text-[10px] leading-snug text-titanium">
          {currentTask}
        </div>
      ) : null}

      <div className="relative">
        {ring.pulse ? (
          <div className="absolute inset-0 animate-ping rounded-full border-2 border-copper opacity-30" />
        ) : null}
        {ring.blink ? (
          <div
            className={cn(
              "absolute inset-0 rounded-full border-2 border-titanium/60",
              "animate-pulse",
            )}
          />
        ) : null}
        <div
          className={cn(
            "relative flex h-16 w-16 items-center justify-center rounded-full border-2 bg-obsidian-2 text-2xl",
            ring.ring,
            isIdle && "grayscale",
          )}
          style={{ borderColor: isIdle ? undefined : colors.border }}
        >
          {emoji}
          {status === "error" ? (
            <span className="absolute -right-1 -top-1 text-sm" aria-hidden>
              ⚠️
            </span>
          ) : null}
        </div>
      </div>

      <div className="text-center">
        <p className="font-title text-sm font-medium text-ivory">{name}</p>
        <p className="font-body text-[11px]" style={{ color: colors.main }}>
          {role}
        </p>
      </div>
    </button>
  );
}
