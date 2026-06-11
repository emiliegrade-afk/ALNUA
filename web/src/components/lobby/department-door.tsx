"use client";

import Link from "next/link";

export interface DepartmentDoorProps {
  icon: string;
  title: string;
  subtitle: string;
  description: string;
  color: string;
  href: string;
  badge?: string;
  stats?: string;
}

export function DepartmentDoor({
  icon,
  title,
  subtitle,
  description,
  color,
  href,
  badge,
  stats,
}: DepartmentDoorProps) {
  return (
    <Link href={href} className="group block">
      <div
        className="relative rounded-xl border bg-[#111827] p-6 transition-all duration-200 cursor-pointer hover:shadow-lg"
        style={{
          borderColor: `${color}33`,
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = `${color}66`;
          e.currentTarget.style.boxShadow = `0 10px 25px -5px ${color}14`;
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = `${color}33`;
          e.currentTarget.style.boxShadow = "none";
        }}
      >
        <div
          className="absolute left-0 top-4 bottom-4 w-[3px] rounded-full"
          style={{ backgroundColor: color }}
        />

        <div className="pl-4">
          <div className="mb-3 flex items-start justify-between">
            <span className="text-2xl">{icon}</span>
            {badge ? (
              <span
                className="rounded-full px-2 py-1 text-xs font-medium"
                style={{ color, backgroundColor: `${color}1A` }}
              >
                {badge}
              </span>
            ) : null}
          </div>
          <h3 className="mb-1 font-semibold text-white">{title}</h3>
          <p className="text-sm text-gray-400">{subtitle}</p>
          {stats ? (
            <p className="mt-3 text-xs" style={{ color: `${color}B3` }}>
              {stats}
            </p>
          ) : (
            <p className="mt-3 text-xs text-gray-500">{description}</p>
          )}
        </div>
      </div>
    </Link>
  );
}
