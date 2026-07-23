"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { BureauAgentsSection } from "@/components/shared/bureau-agents-section";
import { BureauPage } from "@/components/shared/bureau-page";
import { BureauPanel } from "@/components/shared/bureau-panel";
import { Button } from "@/components/ui/button";

const NadiaDesktopPanel = dynamic(
  () =>
    import("@/components/secretary/nadia-desktop-panel").then((m) => ({
      default: m.NadiaDesktopPanel,
    })),
  { loading: () => <PanelSkeleton label="Nadia Desktop" /> },
);

const SavLitePanel = dynamic(
  () =>
    import("@/components/secretary/sav-lite-panel").then((m) => ({
      default: m.SavLitePanel,
    })),
  { loading: () => <PanelSkeleton label="SAV" /> },
);

const AssistantChat = dynamic(
  () =>
    import("@/components/assistant/assistant-chat").then((m) => ({
      default: m.AssistantChat,
    })),
  { loading: () => <PanelSkeleton label="Assistant" /> },
);

const SecretaryConsole = dynamic(
  () =>
    import("@/components/secretary/secretary-console").then((m) => ({
      default: m.SecretaryConsole,
    })),
  { loading: () => <PanelSkeleton label="Console secrétariat" /> },
);

function PanelSkeleton({ label }: { label: string }) {
  return (
    <div className="h-32 animate-pulse rounded-2xl border border-bronze-faint bg-obsidian/70">
      <p className="p-4 text-sm text-titane/50">Chargement {label}…</p>
    </div>
  );
}

export default function SecretaryPage() {
  return (
    <BureauPage
      dept="secretary"
      title="Secrétariat de Direction"
      subtitle="Nadia Faure · Emails · Agenda · Contrats · Réunions"
      breadcrumb="Secrétariat"
    >
      <BureauAgentsSection bureau="secretary" className="grid gap-4 sm:grid-cols-1" />

      <NadiaDesktopPanel />
      <SavLitePanel />

      <BureauPanel noPadding>
        <AssistantChat defaultAgent="secretary" variant="secretary" />
      </BureauPanel>

      <SecretaryConsole />

      <div className="flex flex-wrap gap-3">
        <Button asChild variant="outline" className="border-bronze-faint hover:border-bronze/40">
          <Link href="/ceo">Bureau du CEO</Link>
        </Button>
        <Button asChild variant="outline" className="border-bronze-faint hover:border-bronze/40">
          <Link href="/hub">Direction — COO</Link>
        </Button>
      </div>
    </BureauPage>
  );
}
