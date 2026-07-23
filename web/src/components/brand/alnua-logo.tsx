"use client";

import Image from "next/image";
import { cn } from "@/lib/utils";

type LogoVariant = "lockup" | "symbol" | "icon" | "ring";

interface AlnuaLogoProps {
  variant?: LogoVariant;
  className?: string;
  height?: number;
  size?: number;
  withWordmark?: boolean;
  animated?: boolean;
  staticMark?: boolean;
}

const MARK_SRC = "/brand/alnua-mark.png";
const LOCKUP_SRC = "/brand/alnua-lockup.png";

/**
 * Logo ALNUA — assets DA officiels (mark circulaire + lockup PNG).
 */
export function AlnuaLogo({
  variant = "icon",
  className,
  height,
  size,
  withWordmark = false,
  animated = true,
  staticMark = false,
}: AlnuaLogoProps) {
  const markOnly = variant === "icon" || variant === "symbol";
  const showWordmark = withWordmark || variant === "lockup";
  const dim =
    size ??
    height ??
    (variant === "lockup" ? 52 : variant === "icon" ? 32 : 44);
  const anim = animated && !staticMark;

  if (variant === "lockup") {
    return (
      <div className={cn("flex flex-col items-center", className)} role="img" aria-label="ALNUA">
        <Image
          src={LOCKUP_SRC}
          alt="ALNUA"
          width={Math.round(dim * 2.4)}
          height={Math.round(dim * 1.1)}
          className="h-auto w-auto max-h-[88px] object-contain"
          priority
        />
      </div>
    );
  }

  return (
    <div className={cn("flex items-center gap-3", className)} role="img" aria-label="ALNUA">
      <Image
        src={MARK_SRC}
        alt=""
        width={dim}
        height={dim}
        className={cn(
          "shrink-0 object-contain",
          variant === "ring" && "drop-shadow-[0_0_12px_rgba(192,138,98,0.35)]",
          anim && "animate-alnua-glow",
        )}
        priority
      />

      {showWordmark && !markOnly ? (
        <div className="flex flex-col leading-none font-title">
          <span className="text-xl font-medium tracking-[0.35em] text-gradient-bronze">
            ALNUA
          </span>
          <span className="mt-1 text-[9px] tracking-[0.38em] text-titane/70">
            VIRTUAL AI ENTERPRISE
          </span>
        </div>
      ) : null}
    </div>
  );
}

export function AlnuaWordmark({ className }: { className?: string }) {
  return (
    <p
      className={cn(
        "font-title text-sm font-medium tracking-[0.35em] text-gradient-bronze",
        className,
      )}
    >
      ALNUA
    </p>
  );
}
