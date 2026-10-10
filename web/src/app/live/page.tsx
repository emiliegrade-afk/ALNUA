"use client";

import { C } from "@/app/app-v2/shared";
import { ConsoleProvider } from "@/components/console/console-provider";
import { DeptV2PageShell } from "@/components/dept-v2";
import { LiveCockpit } from "@/components/live/live-cockpit";
import { ROUTES } from "@/lib/routes";

/** Cockpit Nadia — tâches en arrière-plan et écrans de résultats (DEC-038). */
export default function LivePage() {
  return (
    <ConsoleProvider>
      <DeptV2PageShell
        deptHref={ROUTES.secretary}
        activeDeptId="secretary"
        coreSubtitle="Nadia Live"
      >
        <div
          className="alnua-scroll flex min-h-0 min-w-0 flex-1 flex-col overflow-y-auto px-4 pb-4 pt-3.5"
          style={{ color: C.ivory }}
        >
          <LiveCockpit />
        </div>
      </DeptV2PageShell>
    </ConsoleProvider>
  );
}
