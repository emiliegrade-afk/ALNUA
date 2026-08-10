"use client";

import { C } from "@/app/app-v2/shared";

/** Section nav — void + filet, jamais de fond gris. */
export function DeptV2SectionBox({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className="border border-titanium/15 bg-transparent p-1.5"
      style={{ borderColor: "rgba(167,173,181,0.14)" }}
    >
      <p
        className="mb-1.5 ml-2 mt-1 text-[8px] font-medium uppercase tracking-[0.22em]"
        style={{ color: C.titaniumDim }}
      >
        {title}
      </p>
      {children}
    </div>
  );
}
