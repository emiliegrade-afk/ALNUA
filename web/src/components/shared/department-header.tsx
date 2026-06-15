"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { DEPT_COLORS, type DeptKey } from "@/lib/dept-colors";
import { prefetchLobby } from "@/lib/hq-prefetch";
import { useHubNavigate } from "@/components/layout/hub-navigation";

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
  const router = useRouter();
  const { navigate } = useHubNavigate();
  const colors = DEPT_COLORS[dept];

  useEffect(() => {
    prefetchLobby(router);
  }, [router]);

  return (
    <header className="mb-8 pt-12">
      <nav className="mb-3 flex items-center gap-2 font-body text-sm text-titanium/60">
        <button
          type="button"
          onClick={() => navigate("/")}
          className="transition hover:text-titanium"
        >
          Lobby
        </button>
        <span>/</span>
        <span style={{ color: colors.main }}>{breadcrumb ?? title}</span>
      </nav>

      <div className="flex items-center gap-3">
        <span
          className="h-3 w-3 rounded-full"
          style={{ backgroundColor: colors.main }}
        />
        <div>
          <h1 className="font-title text-2xl font-semibold text-ivory">
            {title}
          </h1>
          {subtitle ? (
            <p className="mt-1 font-body text-sm text-titanium">{subtitle}</p>
          ) : null}
        </div>
      </div>
    </header>
  );
}
