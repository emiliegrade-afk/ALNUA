"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useHubNavigate } from "@/components/layout/hub-navigation";
import { ArrowRight, MessageSquare } from "lucide-react";
import { AgentOfficeAvatar } from "@/components/openroom/agent-office-avatar";
import { getAgentOfficeAssets } from "@/lib/agent-assets";
import {
  getOfficeBadge,
  getPrimaryAgentForOffice,
  type HqSector,
} from "@/lib/hq-hub-offices";
import type { LobbyStats } from "@/lib/lobby-api";
import type { AgentStatus } from "@/lib/openroom-api";
import { DEPT_COLORS } from "@/lib/dept-colors";
import { cn } from "@/lib/utils";

interface HqAgentPanelProps {
  stats: LobbyStats;
  agents: Record<string, AgentStatus>;
  selectedOffice: HqSector | null;
}

export function HqAgentPanel({
  stats,
  agents,
  selectedOffice,
}: HqAgentPanelProps) {
  const { navigate } = useHubNavigate();
  const [draft, setDraft] = useState("");

  const agent = selectedOffice ? getPrimaryAgentForOffice(selectedOffice) : null;
  const isCeoOffice = selectedOffice?.id === "ceo";
  const offMapPortrait =
    selectedOffice && "portrait" in selectedOffice
      ? selectedOffice.portrait
      : undefined;
  const status = agent
    ? (agents[agent.id] ?? { status: "idle" as const })
    : null;
  const officeAssets = agent ? getAgentOfficeAssets(agent.id) : null;
  const badge = selectedOffice ? getOfficeBadge(selectedOffice, stats) : null;
  const deptColor = selectedOffice ? DEPT_COLORS[selectedOffice.dept].main : undefined;

  return (
    <aside className="flex h-full flex-col border-l border-copper/15 bg-obsidian/60 backdrop-blur-xl">
      <div className="flex items-center gap-2 border-b border-copper/10 px-4 py-3">
        <MessageSquare className="h-4 w-4 text-copper" />
        <span className="font-body text-[10px] uppercase tracking-[0.2em] text-copper/80">
          Agent Window
        </span>
      </div>

      {selectedOffice ? (
        <>
          {agent && status ? (
            <div
              className="relative mx-3 mt-3 overflow-hidden rounded-lg border border-copper/20"
              style={{
                boxShadow: deptColor ? `0 0 40px ${deptColor}22` : undefined,
              }}
            >
              {officeAssets ? (
                <AgentOfficeAvatar
                  agentId={agent.id}
                  name={agent.name}
                  role={agent.role}
                  branch={agent.branch}
                  status={status.status}
                  currentTask={status.currentTask}
                  variant="compact"
                />
              ) : (
                <div className="flex flex-col items-center gap-2 bg-gradient-to-b from-obsidian/80 to-obsidian px-4 py-8">
                  <span className="text-5xl">{agent.icon}</span>
                  <p className="font-title text-sm font-medium text-ivory">
                    {agent.name}
                  </p>
                  <p className="font-body text-xs text-titanium">{agent.role}</p>
                  <span
                    className={cn(
                      "rounded-full px-2 py-0.5 font-body text-[10px] capitalize",
                      status.status === "working"
                        ? "bg-emerald-500/20 text-emerald-400"
                        : status.status === "waiting"
                          ? "bg-amber-500/20 text-amber-400"
                          : "bg-titanium/10 text-titanium",
                    )}
                  >
                    {status.status}
                  </span>
                </div>
              )}
            </div>
          ) : isCeoOffice && offMapPortrait ? (
            <div className="relative mx-3 mt-3 overflow-hidden rounded-lg border border-copper/20">
              <div className="relative aspect-[4/3] w-full bg-obsidian">
                <Image
                  src={offMapPortrait}
                  alt="Emilie — CEO"
                  fill
                  className="object-cover object-top"
                  sizes="280px"
                />
              </div>
              <div className="border-t border-copper/10 bg-obsidian/80 px-3 py-2">
                <p className="font-title text-sm font-medium text-ivory">Emilie</p>
                <p className="font-body text-xs text-titanium">CEO · ALNUA</p>
              </div>
            </div>
          ) : (
            <div className="mx-3 mt-3 flex flex-col items-center gap-2 rounded-lg border border-copper/20 bg-obsidian/60 px-4 py-8">
              <span className="text-4xl">{selectedOffice.icon}</span>
              <p className="font-body text-xs text-titanium">Bureau département</p>
            </div>
          )}

          <div className="mx-3 mt-3 space-y-1">
            <p className="font-title text-sm font-medium text-ivory">
              {selectedOffice.title}
            </p>
            <p className="font-body text-[11px] text-titanium">
              {selectedOffice.subtitle}
            </p>
            {badge ? (
              <p
                className={cn(
                  "inline-block rounded px-1.5 py-0.5 font-body text-[10px]",
                  badge.highlight
                    ? "bg-copper/20 text-copper"
                    : "bg-white/5 text-titanium",
                )}
              >
                {badge.label}
              </p>
            ) : null}
          </div>

          {status?.currentTask ? (
            <div className="mx-3 mt-3 rounded-lg border border-copper/10 bg-obsidian/80 p-3">
              <p className="mb-1 font-body text-[9px] uppercase tracking-wider text-titanium/50">
                Tâche en cours
              </p>
              <p className="font-body text-xs text-ivory">{status.currentTask}</p>
            </div>
          ) : null}

          {agent ? (
            <div className="mx-3 mt-3 flex-1">
              <textarea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder={`Message à ${agent.name.split(" ")[0]}…`}
                rows={3}
                className="w-full resize-none rounded-lg border border-copper/15 bg-obsidian/80 px-3 py-2 font-body text-xs text-ivory placeholder:text-titanium/40 focus:border-copper/40 focus:outline-none"
              />
              <Link
                href={`/openroom?agent=${agent.id}`}
                className="mt-2 flex w-full items-center justify-center gap-2 rounded-lg border border-copper/20 bg-copper/10 py-2 font-body text-xs text-copper transition hover:bg-copper/20"
              >
                <MessageSquare className="h-3.5 w-3.5" />
                Ouvrir le chat
              </Link>
            </div>
          ) : isCeoOffice ? (
            <div className="mx-3 mt-3">
              <Link
                href="/ceo"
                className="flex w-full items-center justify-center gap-2 rounded-lg border border-copper/20 bg-copper/10 py-2 font-body text-xs text-copper transition hover:bg-copper/20"
              >
                Ouvrir le cockpit CEO
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          ) : null}

          <button
            type="button"
            onClick={() => navigate(selectedOffice.href)}
            className="mx-3 mb-3 flex items-center justify-center gap-2 rounded-lg bg-copper py-2.5 font-title text-xs font-medium text-obsidian transition hover:bg-copper/90"
          >
            Entrer dans le bureau
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </>
      ) : (
        <div className="flex flex-1 flex-col items-center justify-center gap-3 px-6 text-center">
          <span className="text-4xl opacity-40">🏢</span>
          <p className="font-title text-sm text-ivory/80">
            Sélectionne un bureau
          </p>
          <p className="font-body text-[11px] text-titanium/60">
            Clique sur une salle dans la carte pour voir l&apos;agent et
            discuter.
          </p>
          <Link
            href="/openroom"
            className="mt-2 font-body text-[11px] text-copper hover:underline"
          >
            OpenRoom →
          </Link>
        </div>
      )}
    </aside>
  );
}
