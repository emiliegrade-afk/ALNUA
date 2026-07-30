"use client";

import type { ReactNode } from "react";
import { DepartmentHeader } from "@/components/shared/department-header";
import { ActivityRail } from "@/components/shared/activity-rail";
import type { BureauKey } from "@/lib/agent-bureau";
import type { DeptKey } from "@/lib/dept-colors";
import { cn } from "@/lib/utils";

interface BureauPageProps {
  dept: DeptKey;
  title: string;
  subtitle?: string;
  breadcrumb?: string;
  /** Bureau opérationnel du pôle — active la pastille « N agents actifs » et
   * la délégation contextualisée dans l'en-tête. Absent sur les pages sans
   * roster propre (ex. /brand). */
  bureau?: BureauKey;
  children: ReactNode;
  className?: string;
  /** Full-bleed layout (e.g. R&D tabs) */
  flush?: boolean;
  /** Opt out of the persistent activity rail (e.g. pages with their own
   * live-activity view already, or no room for it). Shown by default. */
  hideActivityRail?: boolean;
}

/** Shared shell for bureau / pole pages — matches Hub dashboard DA. */
export function BureauPage({
  dept,
  title,
  subtitle,
  breadcrumb,
  bureau,
  children,
  className,
  flush = false,
  hideActivityRail = false,
}: BureauPageProps) {
  return (
    <div
      className={cn(
        "bureau-page w-full",
        // `max-w` relâché à partir de 2xl : à 1400px, une fois la sidebar et
        // le rail d'activité déduits, le workspace tombait à ~1090px — moins
        // que la maquette de référence n'en a sur un écran de 1536. Les
        // colonnes (discussion, mission) s'y écrasaient jusqu'à l'illisible.
        flush ? "space-y-5" : "mx-auto max-w-[1400px] 2xl:max-w-none",
        flush ? "space-y-5" : "space-y-6",
        className,
      )}
    >
      <DepartmentHeader
        dept={dept}
        title={title}
        subtitle={subtitle}
        breadcrumb={breadcrumb}
        bureau={bureau}
      />
      {/* Le rail ne prend sa colonne qu'à partir de 1440px — c'est aussi le
          seuil auquel il s'ouvre tout seul. En dessous il passe en bande
          pleine largeur sous le contenu, au lieu de voler 320px à un
          workspace déjà à l'étroit. */}
      {hideActivityRail ? (
        children
      ) : (
        <div className="flex flex-col gap-6 min-[1440px]:flex-row min-[1440px]:items-start">
          <div className="min-w-0 flex-1 space-y-6">{children}</div>
          <ActivityRail />
        </div>
      )}
    </div>
  );
}
