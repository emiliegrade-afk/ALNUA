"use client";

import Link from "next/link";
import { AgentAvatar } from "@/components/shared/agent-avatar";

type Props = {
  agentId: string;
  name: string;
  role: string;
  href?: string;
  hrefLabel?: string;
};

/** Compact bureau identity strip (H5 polish). */
export function BureauIdentityStrip({
  agentId,
  name,
  role,
  href,
  hrefLabel,
}: Props) {
  return (
    <div className="flex items-center gap-3 border border-copper/25 bg-transparent px-3 py-2.5">
      <AgentAvatar agentId={agentId} name={name} size={48} ring />
      <div className="min-w-0 flex-1">
        <p className="truncate font-title text-sm text-ivory">{name}</p>
        <p className="truncate text-[11px] text-titanium/65">{role}</p>
      </div>
      {href && hrefLabel ? (
        <Link
          href={href}
          className="shrink-0 text-[11px] uppercase tracking-wider text-copper hover:underline"
        >
          {hrefLabel}
        </Link>
      ) : null}
    </div>
  );
}
