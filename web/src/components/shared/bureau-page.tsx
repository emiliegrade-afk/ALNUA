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
}: BureauPageProps) {
  return (
    <div
      className={cn(
        "bureau-page w-full",
        flush ? "space-y-5" : "mx-auto max-w-[1400px] space-y-6",
        className,
      )}
    >
      <DepartmentHeader
        dept={dept}
        title={title}
        subtitle={subtitle}
        breadcrumb={breadcrumb}
      />
      {children}
    </div>
  );
}
