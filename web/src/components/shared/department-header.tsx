"use client";

import Link from "next/link";
import { DEPT_COLORS, type DeptKey } from "@/lib/dept-colors";

interface DepartmentHeaderProps {
  dept: DeptKey;
  title: string;
  subtitle?: string;
  breadcrumb?: string;
}

export function DepartmentHeader({
  dept,
  title,
  subtitle,
  breadcrumb,
}: DepartmentHeaderProps) {
  const colors = DEPT_COLORS[dept];

  return (
    <header className="mb-8 pt-12">
      <nav className="mb-3 flex items-center gap-2 text-sm text-gray-500">
        <Link href="/" className="transition hover:text-gray-300">
          Lobby
        </Link>
        <span>/</span>
        <span style={{ color: colors.main }}>{breadcrumb ?? title}</span>
      </nav>

      <div className="flex items-center gap-3">
        <span
          className="h-3 w-3 rounded-full"
          style={{ backgroundColor: colors.main }}
        />
        <div>
          <h1 className="text-2xl font-semibold text-white">{title}</h1>
          {subtitle ? (
            <p className="mt-1 text-sm text-gray-400">{subtitle}</p>
          ) : null}
        </div>
      </div>
    </header>
  );
}
