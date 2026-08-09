"use client";

import { useEffect, useState } from "react";
import {
  CAMPAIGN_PLATFORM_LABELS,
  CAMPAIGN_STATUS_COLORS,
  CAMPAIGN_STATUS_LABELS,
} from "@/components/marketing/campaign.constants";
import { fetchCampaigns, type Campaign } from "@/lib/marketing-api";
import { formatCurrency } from "@/lib/finances-api";
import { C } from "@/app/app-v2/shared";
import { PremiumPanel, PlatformBadge, MONO } from "@/app/marketing-v2/premium";

/* "Campagnes actives" — Vue Globale Marketing (Phase 38, échelle premium).
   Aperçu réel des campagnes Phase 33 (budget alloué vs spent_usd) + ROI/
   reach quand une stat a été saisie manuellement (Phase 37) — jamais un
   ROI affiché s'il n'a pas été renseigné. */

export function CampaignsPreviewPanel({ onSeeAll }: { onSeeAll?: () => void }) {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchCampaigns({ status: "active" })
      .then((c) => {
        if (!cancelled) setCampaigns(c.sort((a, b) => b.spent_usd - a.spent_usd).slice(0, 5));
      })
      .catch(() => {
        if (!cancelled) setCampaigns([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <PremiumPanel
      title="Campagnes actives"
      action={
        onSeeAll ? (
          <button type="button" onClick={onSeeAll} className="text-[11px]" style={{ color: C.copperLight }}>
            Voir toutes →
          </button>
        ) : undefined
      }
    >
      {loading && campaigns.length === 0 ? (
        <p className="text-[11px]" style={{ color: C.faint }}>
          Chargement…
        </p>
      ) : campaigns.length === 0 ? (
        <p className="text-[11px]" style={{ color: C.faint }}>
          Aucune campagne active pour l&apos;instant.
        </p>
      ) : (
        <div className="flex flex-col">
          {campaigns.map((c) => (
            <div key={c.id} className="flex items-center gap-3 border-b py-2.5 last:border-none last:pb-0" style={{ borderColor: C.line }}>
              <PlatformBadge platform={c.platform} />
              <div className="min-w-0 flex-1">
                <p className="truncate text-[12.5px] font-semibold" style={{ color: C.ivory }}>
                  {c.name}
                </p>
                <p className="mt-0.5 text-[10.5px]" style={{ color: C.faint }}>
                  {CAMPAIGN_PLATFORM_LABELS[c.platform] ?? c.platform}
                </p>
              </div>
              <div className="shrink-0 text-right">
                <p className="text-[13px] font-semibold" style={{ fontFamily: MONO, color: C.copperLight }}>
                  {c.roi_pct != null ? `${c.roi_pct > 0 ? "+" : ""}${c.roi_pct}%` : `${formatCurrency(c.spent_usd)} / ${formatCurrency(c.budget_allocated_usd)}`}
                </p>
                <p className="mt-0.5 text-[10px]" style={{ color: C.faint }}>
                  {c.roi_pct != null ? `${formatCurrency(c.spent_usd)} dépensé` : `${c.budget_allocated_usd > 0 ? Math.min(100, Math.round((c.spent_usd / c.budget_allocated_usd) * 100)) : 0}% du budget`}
                </p>
              </div>
              <span
                className="shrink-0 rounded-full px-[9px] py-[3px] text-[9.5px] font-semibold"
                style={{ color: CAMPAIGN_STATUS_COLORS[c.status], background: "rgba(111,207,151,.1)" }}
              >
                {CAMPAIGN_STATUS_LABELS[c.status]}
              </span>
            </div>
          ))}
        </div>
      )}
    </PremiumPanel>
  );
}
