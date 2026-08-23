"use client";

import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils";

/** Vertical snap rail — cards CEO (dossiers / workflows), slide haut → bas. */
export function CeoSlideRail({
  children,
  className,
  ariaLabel,
  maxHeightClass = "max-h-[280px]",
}: {
  children: ReactNode;
  className?: string;
  ariaLabel: string;
  /** Cap height so the page stays compact; content scrolls inside. */
  maxHeightClass?: string;
}) {
  return (
    <div
      role="list"
      aria-label={ariaLabel}
      className={cn(
        "alnua-scroll flex snap-y snap-mandatory flex-col gap-3 overflow-y-auto overflow-x-hidden pr-1",
        "[scrollbar-width:thin]",
        maxHeightClass,
        className,
      )}
    >
      {children}
    </div>
  );
}

type SlideProps = {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
  interactive?: boolean;
} & Omit<HTMLAttributes<HTMLDivElement>, "className" | "children" | "onClick">;

/** Snap slide vertical — pleine largeur. */
export function CeoSlideCard({
  children,
  className,
  onClick,
  interactive = Boolean(onClick),
  ...rest
}: SlideProps) {
  const base = cn(
    "w-full shrink-0 snap-start rounded-xl border border-copper/25 bg-obsidian-deep/50 p-3 text-left transition",
    "hover:border-copper/50 hover:bg-copper/[0.06]",
    interactive &&
      "cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-copper/40",
    className,
  );

  if (interactive) {
    return (
      <div
        role="listitem"
        tabIndex={0}
        className={base}
        onClick={onClick}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onClick?.();
          }
        }}
        {...rest}
      >
        {children}
      </div>
    );
  }

  return (
    <div role="listitem" className={base} {...rest}>
      {children}
    </div>
  );
}
