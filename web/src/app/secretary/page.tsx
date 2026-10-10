"use client";

import Link from "next/link";

import { ConsoleProvider } from "@/components/console/console-provider";
import { DeptV2PageShell } from "@/components/dept-v2";
import { AssistantChat } from "@/components/assistant/assistant-chat";
import { NadiaDesktopPanel } from "@/components/secretary/nadia-desktop-panel";
import { NadiaToolsPanel } from "@/components/secretary/nadia-tools-panel";
import { SavLitePanel } from "@/components/secretary/sav-lite-panel";
import { SecretaryCommandView } from "@/components/siege/secretary-command-view";
import { C } from "@/app/app-v2/shared";
import { NadiaModeRail } from "@/components/live/nadia-mode-rail";
import { ROUTES } from "@/lib/routes";

/** Secrétariat — maquette command center + chat / outils Hub. */
export default function SecretaryPage() {
  return (
    <ConsoleProvider>
      <DeptV2PageShell
        deptHref={ROUTES.secretary}
        activeDeptId="secretary"
        coreSubtitle="Bureau Nadia"
      >
        <div
          className="alnua-scroll flex min-h-0 min-w-0 flex-1 flex-col gap-5 overflow-y-auto px-4 pb-20 pt-3.5"
          style={{ color: C.ivory }}
        >
          <NadiaModeRail />
          <SecretaryCommandView />
          <Link
            href={ROUTES.live}
            className="self-start rounded-lg border border-copper/30 bg-obsidian-2 px-3 py-1.5 text-sm text-copper-light hover:border-copper/60"
          >
            Ouvrir Nadia Live — tâches en arrière-plan
          </Link>
          <NadiaDesktopPanel />
          <div className="min-h-[360px] rounded-xl border border-copper/20 bg-obsidian/40 p-1">
            <AssistantChat variant="secretary" defaultAgent="secretary" embedded />
          </div>
          <NadiaToolsPanel />
          <SavLitePanel />
        </div>
      </DeptV2PageShell>
    </ConsoleProvider>
  );
}
