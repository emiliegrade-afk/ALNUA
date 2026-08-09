"use client";

import { useEffect, useState } from "react";
import { CAMPAIGN_PLATFORM_LABELS } from "@/components/marketing/campaign.constants";
import { fetchPerformanceByPlatform, type PlatformPerformance } from "@/lib/marketing-api";
import { formatCurrency } from "@/lib/finances-api";
import { C } from "@/app/app-v2/shared";
import { PremiumPanel, PlatformBadge, MONO } from "@/app/marketing-v2/premium";

/* "Performances par canal" — Phase 37, ROADMAP.md. Agrège reach/engagements/
   conversions/ROI réels par plateforme ad (meta/google/tiktok), calculés
   côté backend UNIQUEMENT sur les campagnes où Emilie/Léo ont saisi des
   stats manuellement (campagnes actives ou terminées, /campaigns →
   "Modifier" → section Statistiques). sample_size affiché explicitement :
   ce n'est jamais une couverture complète du canal, seulement les
   campagnes suivies jusqu'ici. */

export function PerformanceByPlatformPanel() {
  const [rows, setRows] = useState<PlatformPerformance[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchPerformanceByPlatform()
      .then((r) => {
        if (!cancelled) setRows(r);
      })
      .catch(() => {
        if (!cancelled) setRows([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <PremiumPanel title="Performances par canal">
      {loading && rows.length === 0 ? (
        <p className="text-[11px]" style={{ color: C.faint }}>
          Chargement…
        </p>
      ) : rows.length === 0 ? (
        <p className="text-[11px] leading-relaxed" style={{ color: C.faint }}>
          Aucune statistique saisie pour l&apos;instant. Ouvre une campagne (onglet Campagnes →
          Modifier) pour renseigner reach/engagements/conversions/revenu depuis le dashboard de la
          plateforme.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-[11.5px]" style={{ color: C.warm }}>
            <thead>
              <tr style={{ color: C.faint }}>
                <th className="pb-2 text-left text-[10px] font-normal uppercase tracking-wide">Canal</th>
                <th className="pb-2 text-right text-[10px] font-normal uppercase tracking-wide">Reach</th>
                <th className="pb-2 text-right text-[10px] font-normal uppercase tracking-wide">Engagements</th>
                <th className="pb-2 text-right text-[10px] font-normal uppercase tracking-wide">Conversions</th>
                <th className="pb-2 text-right text-[10px] font-normal uppercase tracking-wide">ROI</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.platform} className="border-t" style={{ borderColor: C.line }}>
                  <td className="py-2.5">
                    <span className="flex items-center gap-2">
                      <PlatformBadge platform={r.platform} size={22} />
                      {CAMPAIGN_PLATFORM_LABELS[r.platform] ?? r.platform}
                      <span className="text-[9.5px]" style={{ color: C.faint }}>
                        · {r.sample_size} campagne{r.sample_size > 1 ? "s" : ""}
                      </span>
                    </span>
                  </td>
                  <td className="py-2.5 text-right tabular-nums" style={{ fontFamily: MONO }}>{r.reach.toLocaleString("fr-FR")}</td>
                  <td className="py-2.5 text-right tabular-nums" style={{ fontFamily: MONO }}>{r.engagements.toLocaleString("fr-FR")}</td>
                  <td className="py-2.5 text-right tabular-nums" style={{ fontFamily: MONO }}>{r.conversions.toLocaleString("fr-FR")}</td>
                  <td className="py-2.5 text-right tabular-nums" style={{ fontFamily: MONO, color: r.roi_pct != null && r.roi_pct >= 0 ? C.online : "#e8746c" }}>
                    {r.roi_pct != null ? `${r.roi_pct > 0 ? "+" : ""}${r.roi_pct}%` : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-3 text-[10px]" style={{ color: C.faint }}>
            Dépensé réel : {rows.map((r) => `${CAMPAIGN_PLATFORM_LABELS[r.platform] ?? r.platform} ${formatCurrency(r.spent_usd)}`).join(" · ")}.
            ROI affiché uniquement si un revenu a été saisi.
          </p>
        </div>
      )}
    </PremiumPanel>
  );
}
