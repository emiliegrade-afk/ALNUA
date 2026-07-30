"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ChevronDown, ChevronRight, Radio } from "lucide-react";
import { useConsoleData } from "@/components/console/console-provider";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { BUREAU_AGENTS } from "@/lib/agent-bureau";
import { ROUTES } from "@/lib/routes";
import { cn } from "@/lib/utils";

/** Le flux d'activité ne porte que le nom affiché de l'agent — on remonte à
 * son id (clé d'avatar) via le roster canonique. */
const AGENT_ID_BY_NAME = new Map(BUREAU_AGENTS.map((a) => [a.name, a.id]));

const KIND_DOT: Record<string, string> = {
  ship: "bg-emerald-400",
  decide: "bg-bronze-bright",
  research: "bg-glow",
  alert: "bg-red-400",
  create: "bg-bronze",
};

/**
 * Rail « Activité en temps réel » des maquettes — horodatage à gauche,
 * portrait de l'agent, action, contexte de département, pastille de nature.
 *
 * Replié par défaut sous ~1440px (sidebar + rail + workspace à onglets
 * deviennent à l'étroit en dessous ; console-topbar.tsx porte déjà un
 * correctif de compression à 1280px, FINDING-002). Jamais masqué : un badge
 * « N nouveaux » le garde visible mais hors du chemin.
 */
export function ActivityRail() {
  const { activityFeed } = useConsoleData();
  const [expanded, setExpanded] = useState(false);
  const [seenCount, setSeenCount] = useState(0);

  useEffect(() => {
    const isWide = window.matchMedia("(min-width: 1440px)").matches;
    setExpanded(isWide);
    if (isWide) setSeenCount(activityFeed.length);
    // Un seul check au montage — pas de resize listener : le choix
    // d'ouverture/fermeture reste ensuite sous le contrôle de l'utilisatrice.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (expanded) setSeenCount(activityFeed.length);
  }, [expanded, activityFeed.length]);

  const unseenCount = Math.max(0, activityFeed.length - seenCount);
  const items = useMemo(() => activityFeed.slice(0, 30), [activityFeed]);

  return (
    <aside className="w-full shrink-0 min-[1440px]:w-[288px]">
      <div className="min-[1440px]:sticky min-[1440px]:top-20">
        <div
          className={cn(
            "flex items-center justify-between gap-2 border border-bronze-faint bg-obsidian-deep/60 pl-4 pr-2 transition-colors",
            expanded ? "rounded-t-xl border-b-0" : "rounded-xl",
          )}
        >
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="flex min-w-0 flex-1 items-center gap-2 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.18em] text-titane/70 transition-colors hover:text-ivoire"
            aria-expanded={expanded}
          >
            <Radio className="h-3.5 w-3.5 shrink-0 text-bronze" />
            <span className="truncate">Activité en temps réel</span>
            {!expanded && unseenCount > 0 ? (
              <span className="shrink-0 rounded-full bg-bronze/15 px-1.5 py-0.5 text-[10px] normal-case tracking-normal text-bronze-bright">
                {unseenCount} nouveau{unseenCount !== 1 ? "x" : ""}
              </span>
            ) : null}
            {expanded ? (
              <ChevronDown className="ml-auto h-3.5 w-3.5 shrink-0 text-titane/50" />
            ) : (
              <ChevronRight className="ml-auto h-3.5 w-3.5 shrink-0 text-titane/50" />
            )}
          </button>
          <Link
            href={ROUTES.activity}
            className="shrink-0 rounded-md px-2 py-1 text-[10px] text-titane/55 transition-colors hover:bg-obsidian hover:text-bronze-bright"
          >
            Tout voir
          </Link>
        </div>

        {expanded ? (
          <div className="flex flex-col rounded-b-xl border border-bronze-faint bg-obsidian/70">
            {items.length === 0 ? (
              <p className="px-4 py-10 text-center text-xs text-titane/50">
                Aucune activité récente — les agents apparaîtront ici dès
                qu&apos;ils agissent.
              </p>
            ) : (
              <ul className="alnua-scroll max-h-[460px] divide-y divide-bronze-faint overflow-y-auto">
                {items.map((item) => {
                  const agentId = AGENT_ID_BY_NAME.get(item.agent);
                  return (
                    <li
                      key={item.id}
                      className="flex items-start gap-2.5 px-3 py-2.5 transition-colors hover:bg-obsidian-deep/40"
                    >
                      <span className="w-9 shrink-0 pt-0.5 font-mono text-[10px] tabular-nums text-titane/40">
                        {item.time}
                      </span>
                      <AgentAvatar
                        agentId={agentId ?? item.agent}
                        name={item.agent}
                        size={24}
                        className="mt-0.5"
                      />
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-xs font-medium text-ivoire/90">
                          {item.agent}
                        </span>
                        <span className="mt-0.5 block text-[11px] leading-snug text-titane/65">
                          {item.action}
                        </span>
                        <span className="mt-0.5 block text-[9px] uppercase tracking-wide text-titane/35">
                          {item.dept}
                        </span>
                      </span>
                      <span
                        className={cn(
                          "mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full",
                          KIND_DOT[item.kind] ?? "bg-titane/40",
                        )}
                        aria-hidden
                      />
                    </li>
                  );
                })}
              </ul>
            )}

            <Link
              href={ROUTES.activity}
              className="flex items-center justify-center gap-1.5 border-t border-bronze-faint px-4 py-2.5 text-[11px] text-titane/65 transition-colors hover:bg-obsidian-deep/50 hover:text-bronze-bright"
            >
              Voir toute l&apos;activité
              <ChevronRight className="h-3 w-3" />
            </Link>
          </div>
        ) : null}
      </div>
    </aside>
  );
}
