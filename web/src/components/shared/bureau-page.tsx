"use client";

import type { ReactNode } from "react";
import { DepartmentHeader } from "@/components/shared/department-header";
import type { DeptKey } from "@/lib/dept-colors";
import { cn } from "@/lib/utils";

interface BureauPageProps {
  dept: DeptKey;
  title: string;
  subtitle?: string;
  breadcrumb?: string;
  children: ReactNode;
  className?: string;
  /** Full-bleed layout (e.g. R&D tabs) */
  flush?: boolean;
  /**
   * Fill the viewport height instead of stacking in normal document flow.
   * For pages with an internal tab area that needs real remaining height
   * (e.g. R&D) rather than a hardcoded `calc(100dvh - Nrem)` guess that
   * drifts out of sync with the actual header height above it. Callers
   * must mark their own non-last children `shrink-0` and give the last
   * (tab content) child `flex-1 min-h-0`.
   */
  fill?: boolean;
}

/** Shared shell for bureau / pole pages — matches Hub dashboard DA. */
export function BureauPage({
  dept,
  title,
  subtitle,
  breadcrumb,
  children,
  className,
  flush = false,
  fill = false,
}: BureauPageProps) {
  return (
    <div
      className={cn(
        "bureau-page w-full",
        fill
          ? "flex h-[calc(100dvh-8rem)] flex-col gap-5 overflow-hidden"
          : flush
            ? "space-y-5"
            : "mx-auto max-w-[1400px] space-y-6",
        className,
      )}
    >
      <DepartmentHeader
        dept={dept}
        title={title}
        subtitle={subtitle}
        breadcrumb={breadcrumb}
        className={fill ? "shrink-0" : undefined}
      />
      {children}
    </div>
  );
}
