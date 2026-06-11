"use client";

import Link from "next/link";
import type { DeptTier } from "@/lib/dept-colors";
import { cn } from "@/lib/utils";

export interface DepartmentDoorProps {
  icon: string;
  title: string;
  subtitle: string;
  description: string;
  href: string;
  tier?: DeptTier;
  badge?: string;
  stats?: string;
}

export function DepartmentDoor({
  icon,
  title,
  subtitle,
  description,
  href,
  tier = "active",
  badge,
  stats,
}: DepartmentDoorProps) {
  return (
    <Link href={href} className="group block">
      <div
        className={cn(
          "alnua-card cursor-pointer pl-0",
          "hover:bg-obsidian-3"
        )}
      >
        <div
          className={cn(
            "absolute left-0 top-4 bottom-4 w-0.5 rounded-full bg-copper",
            tier === "support" && "opacity-50"
          )}
        />

        <div className="pl-4">
          <div className="mb-3 flex items-start justify-between">
            <span className="text-2xl">{icon}</span>
            {badge ? (
              <span className="badge-copper px-2 py-1 text-xs font-medium">
                {badge}
              </span>
            ) : null}
          </div>
          <h3 className="mb-1 font-title text-base font-semibold text-ivory">
            {title}
          </h3>
          <p className="font-body text-sm text-titanium">{subtitle}</p>
          {stats ? (
            <p className="mt-3 font-body text-xs text-copper/70">{stats}</p>
          ) : (
            <p className="mt-3 font-body text-xs text-titanium/60">
              {description}
            </p>
          )}
        </div>
      </div>
    </Link>
  );
}
