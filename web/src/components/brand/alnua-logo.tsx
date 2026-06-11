"use client";

import { cn } from "@/lib/utils";

type LogoVariant = "lockup" | "symbol" | "icon";

const SOURCES: Record<LogoVariant, { src: string; width: number; height: number }> = {
  lockup: { src: "/alnua-logo.png", width: 1024, height: 682 },
  symbol: { src: "/alnua-symbol.png", width: 1024, height: 682 },
  icon: { src: "/alnua-icon.png", width: 1024, height: 682 },
};

interface AlnuaLogoProps {
  variant?: LogoVariant;
  className?: string;
  height?: number;
}

export function AlnuaLogo({
  variant = "lockup",
  className,
  height,
}: AlnuaLogoProps) {
  const { src, width, height: naturalHeight } = SOURCES[variant];
  const displayHeight = height ?? (variant === "lockup" ? 56 : variant === "icon" ? 40 : 48);
  const displayWidth = Math.round((width / naturalHeight) * displayHeight);

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src}
      alt="ALNUA"
      width={displayWidth}
      height={displayHeight}
      className={cn("block object-contain", className)}
    />
  );
}

export function AlnuaWordmark({ className }: { className?: string }) {
  return (
    <p
      className={cn(
        "text-sm font-semibold tracking-[0.35em] text-ivory",
        className
      )}
    >
      ALNUA
    </p>
  );
}
