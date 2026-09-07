"use client";

import Link from "next/link";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { getAgentsForBureau, type BureauKey } from "@/lib/agent-bureau";
import { loungeAgentHref } from "@/lib/routes";

type Props = {
  bureau: BureauKey;
  title?: string;
};

/** Roster with portraits — Direction / Secrétariat. */
export function BureauRoster({ bureau, title = "Équipe" }: Props) {
  const agents = getAgentsForBureau(bureau);
  if (agents.length === 0) return null;

  return (
    <section className="border border-titanium/20 bg-transparent p-3">
      <p className="mb-3 text-[10px] uppercase tracking-[0.2em] text-titanium/55">{title}</p>
      <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {agents.map((a) => (
          <li key={a.id}>
            <Link
              href={loungeAgentHref(a.id)}
              className="flex items-center gap-3 border border-transparent px-1 py-1 transition hover:border-copper/30"
            >
              <AgentAvatar agentId={a.id} name={a.name} size={48} ring />
              <span className="min-w-0">
                <span className="block truncate text-sm text-ivory">{a.name}</span>
                <span className="block truncate text-[11px] text-titanium/60">{a.role}</span>
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
