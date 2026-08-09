"use client";

import { C } from "@/app/app-v2/shared";

export function DeptV2SectionBox({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className="rounded-[10px] border p-2"
      style={{ borderColor: C.line, background: `${C.obsidian2}CC` }}
    >
      <p
        className="mb-2 ml-2 mt-0.5 text-[8.5px] tracking-[0.2em]"
        style={{ color: C.faint }}
      >
        {title}
      </p>
      {children}
    </div>
  );
}
