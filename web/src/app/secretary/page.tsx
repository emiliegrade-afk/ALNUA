"use client";

import { ConsoleProvider } from "@/components/console/console-provider";
import { DeptV2PageShell } from "@/components/dept-v2";
import { AssistantChat } from "@/components/assistant/assistant-chat";
import { NadiaDesktopPanel } from "@/components/secretary/nadia-desktop-panel";
import { NadiaToolsPanel } from "@/components/secretary/nadia-tools-panel";
import { SavLitePanel } from "@/components/secretary/sav-lite-panel";
import { SecretaryCommandView } from "@/components/siege/secretary-command-view";
import { C } from "@/app/app-v2/shared";
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
          className="alnua-scroll flex min-w-0 flex-1 flex-col gap-5 overflow-y-auto px-4 pb-4 pt-3.5"
          style={{ color: C.ivory }}
        >
          <SecretaryCommandView />
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
