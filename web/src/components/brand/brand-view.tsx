"use client";

import { Palette } from "lucide-react";
import { BrandReportModal } from "@/components/brand/brand-report-modal";
import {
  BrandKitLeftColumn,
  BrandKitRightPanel,
} from "@/components/brand/brand-kit-workspace";
import { KitHistory } from "@/components/brand/kit-history";
import { useBrandKitWorkflow } from "@/components/brand/use-brand-kit-workflow";

/** Brand Kit studio — orchestration (panels + history). */
export function BrandView() {
  const w = useBrandKitWorkflow();

  return (
    <div className="space-y-6">
      <header>
        <p className="forge-heading text-[11px] text-copper/80">Studio</p>
        <h1 className="mt-1 flex items-center gap-2 text-2xl font-semibold tracking-wide text-ivory">
          <Palette className="h-6 w-6 text-copper" />
          Brand Kit
        </h1>
        <p className="mt-1 text-sm text-titanium">
          Upload → analyse GPT-4V → 20 formats réseaux sociaux + brand report.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        <BrandKitLeftColumn w={w} />
        <section className="flex min-h-[480px] flex-col rounded-2xl border border-copper/10 bg-obsidian/50 p-5 ring-1 ring-copper/10">
          <h2 className="mb-3 text-xs font-medium uppercase tracking-widest text-titanium">
            Résultats
          </h2>
          <BrandKitRightPanel w={w} />
        </section>
      </div>

      <section className="rounded-2xl border border-copper/10 bg-obsidian/50 p-5 ring-1 ring-copper/10">
        <h2 className="mb-4 text-xs font-medium uppercase tracking-widest text-titanium">
          Historique des kits
        </h2>
        <KitHistory
          kits={w.kitHistory}
          activeKitId={w.activeKitId}
          onSelect={w.handleLoadKit}
          loading={w.historyLoading}
        />
      </section>

      <BrandReportModal
        open={w.reportOpen}
        onOpenChange={w.setReportOpen}
        brandName={w.brandName}
        reportMarkdown={w.reportMarkdown}
        loading={w.reportLoading}
      />
    </div>
  );
}
