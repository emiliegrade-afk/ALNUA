"use client";

import Link from "next/link";
import { HQ_OFF_MAP_ACCESS, getPrimaryAgentForOffice } from "@/lib/hq-hub-offices";
import { AgentAvatar } from "@/components/shared/agent-avatar";

/** Raccourcis hors plan (juridique, bibliothèque, IDE, admin). */
export function HqOffMapRail() {
  return (
    <aside className="space-y-2">
      <p className="label-caps text-copper">Accès rapides</p>
      <ul className="space-y-2">
        {HQ_OFF_MAP_ACCESS.map((sector) => {
          const agent = getPrimaryAgentForOffice(sector);
          return (
            <li key={sector.id}>
              <Link
                href={sector.href}
                className="flex items-center gap-3 rounded-lg border border-copper/20 bg-obsidian-2/80 px-3 py-2.5 transition hover:border-copper/45 hover:bg-obsidian-1"
              >
                {agent ? (
                  <AgentAvatar agentId={agent.id} name={agent.name} size={36} />
                ) : (
                  <span className="text-xl">{sector.icon}</span>
                )}
                <span className="min-w-0">
                  <span className="block truncate text-sm text-ivory">{sector.shortcutLabel}</span>
                  <span className="block truncate text-[11px] text-titanium/60">
                    {sector.subtitle}
                  </span>
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
