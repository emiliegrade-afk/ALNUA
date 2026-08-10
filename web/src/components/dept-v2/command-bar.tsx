"use client";

import { AlnuaStar } from "@/components/brand/alnua-star";
import {
  ALNUA_STAR_GLOW_RGB,
  ALNUA_STAR_SPARK_MID,
  ALNUA_STAR_SPARK_OUTER,
} from "@/app/app-v2/shared";
import { cn } from "@/lib/utils";

export type DeptV2CommandAction = {
  icon: string;
  label: string;
  /** Si défini → bouton cuivre (action réelle). Sinon libellé décoratif. */
  onClick?: () => void;
};

/**
 * Barre de commande départements — void + filet titane, X ALNUA centré
 * animé (émergence). Remplace l'ancienne pill cuivre / orbe.
 */
export function DeptV2CommandBar({
  prompt = "Que souhaitez-vous faire ?",
  actions,
  className,
}: {
  prompt?: string;
  actions: readonly DeptV2CommandAction[];
  className?: string;
}) {
  return (
    <div className={cn("dept-cmd relative mt-auto shrink-0", className)}>
      <span className="z-[1] justify-self-start text-[11px] tracking-wide text-titanium/50 max-sm:hidden">
        {prompt}
      </span>
      <div className="relative z-[3] flex items-center justify-center">
        <AlnuaStar
          size={46}
          glow
          animated
          sparkMid={ALNUA_STAR_SPARK_MID}
          sparkOuter={ALNUA_STAR_SPARK_OUTER}
          glowColorRgb={ALNUA_STAR_GLOW_RGB}
        />
      </div>
      <div className="relative z-[1] flex items-center justify-end gap-4 justify-self-end text-[11px] text-titanium">
        {actions.map((qa) =>
          qa.onClick ? (
            <button
              key={qa.label}
              type="button"
              onClick={qa.onClick}
              title={qa.label}
              className="flex items-center gap-2 bg-metal-copper px-2.5 py-1 text-[11px] font-medium tracking-wide transition-opacity hover:opacity-90"
            >
              <span className="text-[10px]">{qa.icon}</span>
              <span>{qa.label}</span>
            </button>
          ) : (
            <span
              key={qa.label}
              title={qa.label}
              className="hidden items-center gap-1.5 text-titanium/55 xl:flex"
            >
              <span className="text-[10px] text-metal-copper">{qa.icon}</span>
              {qa.label}
            </span>
          ),
        )}
      </div>
    </div>
  );
}
