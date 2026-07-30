"use client";

import { AlnuaStar } from "@/components/brand/alnua-star";
import { useConsoleData } from "./console-provider";
import { useHubHealthLive } from "@/hooks/use-hub-health-live";
import { cn } from "@/lib/utils";

/**
 * Widget « ALNUA CORE » en pied de sidebar, repris de la maquette de
 * référence : titre encadré de deux filets dégradés, cinq ellipses orbitales
 * et la marque ALNUA en cœur lumineux, puis l'état système.
 *
 * Toutes les coordonnées SVG sont littérales : ce composant est rendu côté
 * serveur puis hydraté, et des valeurs calculées en flottant provoquent le
 * même mismatch d'hydratation que celui corrigé sur `CommGraph`
 * (`charts.tsx`).
 */
export function AlnuaCoreWidget() {
  const { activeAgents, totalAgents, stats } = useConsoleData();
  const { phase } = useHubHealthLive();

  const healthy = phase === "ok" || phase === "key";
  const label = healthy
    ? "Tous les systèmes\nopérationnels"
    : phase === "checking"
      ? "Synchronisation\nen cours…"
      : "API Hub\ninjoignable";

  return (
    <div
      className="relative overflow-hidden rounded-xl border p-3 pb-3.5"
      style={{
        borderColor: "rgba(192,138,114,.2)",
        background:
          "radial-gradient(120% 90% at 50% 45%, rgba(192,138,114,.13), rgba(8,10,14,.9) 70%)",
      }}
    >
      <div className="flex items-center justify-center gap-2">
        <span className="h-px w-4 bg-gradient-to-r from-transparent to-copper/60" />
        <span className="text-[10px] tracking-[0.24em] text-copper-light">ALNUA CORE</span>
        <span className="h-px w-4 bg-gradient-to-r from-copper/60 to-transparent" />
      </div>
      <p className="mt-0.5 text-center text-[9.5px] text-titane/70">Système opérationnel</p>

      <div className="relative mt-1.5 flex h-[112px] items-center justify-center">
        <svg
          width="168"
          height="112"
          viewBox="0 0 168 112"
          className="absolute inset-0 m-auto"
          aria-hidden
        >
          <g fill="none" stroke="rgba(192,138,114,.35)">
            <ellipse cx="84" cy="56" rx="78" ry="30" />
            <ellipse cx="84" cy="56" rx="60" ry="46" stroke="rgba(192,138,114,.22)" />
            <ellipse cx="84" cy="56" rx="44" ry="17" />
            <ellipse cx="84" cy="56" rx="26" ry="34" stroke="rgba(192,138,114,.2)" />
            <ellipse cx="84" cy="56" rx="20" ry="8" />
          </g>
          <circle cx="162" cy="56" r="2" fill="#D9A88F" />
          <circle cx="84" cy="10" r="1.8" fill="#C08A72" />
          <circle cx="40" cy="56" r="1.6" fill="#C08A72" />
        </svg>
        <AlnuaStar size={52} glow animated={healthy} className="relative" />
      </div>

      <div className="mt-0.5 flex items-center justify-center gap-2">
        <span
          className={cn(
            "h-[7px] w-[7px] shrink-0 rounded-full",
            healthy
              ? "bg-online shadow-[0_0_7px_#7FC98C]"
              : phase === "checking"
                ? "bg-titane/50"
                : "bg-red-400",
          )}
        />
        <p className="whitespace-pre-line text-left text-[9.5px] leading-tight text-titane/75">
          {label}
        </p>
      </div>

      <dl className="mt-3 space-y-1 border-t border-bronze-faint pt-2.5 text-[10.5px]">
        <div className="flex items-center justify-between">
          <dt className="text-titane/60">Agents en ligne</dt>
          <dd className="tabular-nums text-ivoire/90">
            {activeAgents} / {totalAgents}
          </dd>
        </div>
        <div className="flex items-center justify-between">
          <dt className="text-titane/60">Coût / jour</dt>
          <dd className="tabular-nums text-ivoire/90">${stats.costTodayUsd.toFixed(2)}</dd>
        </div>
      </dl>
    </div>
  );
}
