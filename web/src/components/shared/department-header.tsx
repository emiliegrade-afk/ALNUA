"use client";

import { ArrowLeft } from "lucide-react";
import { useHubNavigate } from "@/components/layout/hub-navigation";
import { DEPT_COLORS, type DeptKey } from "@/lib/dept-colors";
import { cn } from "@/lib/utils";

interface DepartmentHeaderProps {
  dept: DeptKey;
  title: string;
  subtitle?: string;
  breadcrumb?: string;
  className?: string;
}

export function DepartmentHeader({
  dept,
  title,
  subtitle,
  breadcrumb,
  className,
}: DepartmentHeaderProps) {
  const { navigate } = useHubNavigate();
  const colors = DEPT_COLORS[dept];
  const crumb = breadcrumb ?? title;

  return (
    <header className={cn("bureau-header", className)}>
      <nav className="mb-4 flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => navigate("/")}
          className="inline-flex items-center gap-1.5 rounded-lg border border-bronze-faint bg-obsidian/70 px-2.5 py-1.5 text-[11px] font-medium uppercase tracking-[0.12em] text-titane/70 transition hover:border-bronze/40 hover:text-ivoire"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Lobby
        </button>
        <span className="text-titane/35">/</span>
        <span
          className="text-[11px] font-medium uppercase tracking-[0.14em]"
          style={{ color: colors.main }}
        >
          {crumb}
        </span>
      </nav>

      <div className="flex items-start gap-3">
        <span
          className="mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full ring-2 ring-bronze/20"
          style={{ backgroundColor: colors.main }}
        />
        <div className="min-w-0">
          <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-titane/50">
            Pôle · {dept}
          </p>
          <h1 className="font-title text-2xl font-semibold tracking-tight text-ivoire sm:text-3xl">
            {title}
          </h1>
          {subtitle ? (
            <p className="mt-1.5 font-body text-sm text-titane/75">{subtitle}</p>
          ) : null}
        </div>
      </div>

      <div className="mt-5 h-px w-full bg-gradient-to-r from-bronze/30 via-bronze/20 to-transparent" />
    </header>
  );
}
