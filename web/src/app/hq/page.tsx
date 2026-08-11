"use client";

import Link from "next/link";
import { ConsoleProvider } from "@/components/console/console-provider";
import { DeptV2PageShell } from "@/components/dept-v2";
import { HqFloorMap } from "@/components/hq/hq-floor-map";
import { HqOffMapRail } from "@/components/hq/hq-off-map-rail";
import { C } from "@/app/app-v2/shared";
import { ROUTES } from "@/lib/routes";

/** Siège immersif — plan des bureaux + raccourcis. */
export default function HqPage() {
  return (
    <ConsoleProvider>
      <DeptV2PageShell deptHref={ROUTES.hq} activeDeptId="hub" coreSubtitle="Siège ALNUA">
        <div
          className="alnua-scroll flex min-w-0 flex-1 flex-col gap-4 overflow-y-auto px-4 pb-4 pt-3.5"
          style={{ color: C.ivory }}
        >
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h1 className="text-[23px] leading-[1.1] tracking-[1px]">
                <span className="font-bold">HQ</span>{" "}
                <span className="font-light tracking-[4px]" style={{ color: C.titanium }}>
                  SIÈGE
                </span>
              </h1>
              <p className="mt-0.5 text-[11px]" style={{ color: C.dim }}>
                Carte immersive des bureaux · clique pour entrer
              </p>
            </div>
            <div className="flex flex-wrap gap-2 text-[11px]">
              <Link href={ROUTES.ceo} className="text-copper hover:underline">
                Bureau CEO
              </Link>
              <span style={{ color: C.dim }}>·</span>
              <Link href={ROUTES.secretary} className="text-copper hover:underline">
                Secrétariat
              </Link>
              <span style={{ color: C.dim }}>·</span>
              <Link href={ROUTES.legal} className="text-copper hover:underline">
                Juridique
              </Link>
              <span style={{ color: C.dim }}>·</span>
              <Link href={ROUTES.openroom} className="text-copper hover:underline">
                Repas / détente
              </Link>
            </div>
          </div>

          <div className="grid gap-4 lg:grid-cols-[1fr_220px]">
            <HqFloorMap />
            <HqOffMapRail />
          </div>
        </div>
      </DeptV2PageShell>
    </ConsoleProvider>
  );
}
