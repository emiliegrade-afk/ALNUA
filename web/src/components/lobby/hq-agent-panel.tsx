"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useHubNavigate } from "@/components/layout/hub-navigation";
import {
  ArrowRight,
  FileCode2,
  MessageSquare,
  ScrollText,
} from "lucide-react";
import { AgentOfficeAvatar } from "@/components/openroom/agent-office-avatar";
import {
  assistantModeForOffice,
  HqCompactChat,
} from "@/components/lobby/hq-compact-chat";
import { getAgentOfficeAssets } from "@/lib/agent-assets";
import { ROUTES, openroomAgentHref } from "@/lib/routes";
import {
  getAgentsForBureau,
  type BureauAgentDef,
} from "@/lib/agent-bureau";
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

type PanelTab = "chat" | "detail";

function agentsForOffice(office: HqSector): BureauAgentDef[] {
  if (office.bureau) return getAgentsForBureau(office.bureau);
  const primary = getPrimaryAgentForOffice(office);
  return primary ? [primary] : [];
}

export function HqAgentPanel({
  stats,
  agents,
  selectedOffice,
}: HqAgentPanelProps) {
  const { navigate } = useHubNavigate();
  const [focusedAgentId, setFocusedAgentId] = useState<string | null>(null);
  const [tab, setTab] = useState<PanelTab>("chat");

  const officeAgents = selectedOffice ? agentsForOffice(selectedOffice) : [];
  const agent =
    officeAgents.find((a) => a.id === focusedAgentId) ??
    (selectedOffice ? getPrimaryAgentForOffice(selectedOffice) : null);

  useEffect(() => {
    if (!selectedOffice) {
      setFocusedAgentId(null);
      return;
    }
    const list = agentsForOffice(selectedOffice);
    const primary = getPrimaryAgentForOffice(selectedOffice);
    setFocusedAgentId(primary?.id ?? list[0]?.id ?? null);
    setTab(assistantModeForOffice(selectedOffice.id) ? "chat" : "detail");
  }, [selectedOffice]);

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
  const deptColor = selectedOffice
    ? DEPT_COLORS[selectedOffice.dept].main
    : undefined;
  const chatMode = selectedOffice
    ? assistantModeForOffice(selectedOffice.id)
    : null;

  return (
    <aside className="flex h-full flex-col border-l border-copper/15 bg-[#050608]/85 backdrop-blur-2xl">
      <div className="flex items-center gap-2 border-b border-copper/10 px-3 py-2.5">
        <MessageSquare className="h-3.5 w-3.5 text-copper" />
        <span className="font-body text-[9px] uppercase tracking-[0.25em] text-copper/80">
          {selectedOffice ? selectedOffice.shortcutLabel : "Bureau"}
        </span>
      </div>

      {selectedOffice ? (
        <div className="flex min-h-0 flex-1 flex-col">
          {officeAgents.length > 1 ? (
            <div className="flex shrink-0 gap-1 overflow-x-auto border-b border-copper/10 px-2 py-1.5">
              {officeAgents.map((a) => {
                const st = agents[a.id]?.status ?? "idle";
                return (
                  <button
                    key={a.id}
                    type="button"
                    onClick={() => setFocusedAgentId(a.id)}
                    className={cn(
                      "shrink-0 rounded-full border px-2 py-0.5 font-body text-[9px] transition",
                      focusedAgentId === a.id
                        ? "border-copper/50 bg-copper/15 text-copper"
                        : "border-copper/15 text-titanium/65 hover:border-copper/30",
                    )}
                  >
                    {a.name.split(" ")[0]}
                    {st === "working" ? " ●" : ""}
                  </button>
                );
              })}
            </div>
          ) : null}

          <div className="relative mx-2 mt-2 shrink-0 overflow-hidden rounded-lg border border-copper/20">
            {agent && status && officeAssets ? (
              <AgentOfficeAvatar
                agentId={agent.id}
                name={agent.name}
                role={agent.role}
                branch={agent.branch}
                status={status.status}
                currentTask={status.currentTask}
                variant="compact"
              />
            ) : isCeoOffice && offMapPortrait ? (
              <div>
                <div className="relative aspect-[2/1] w-full bg-obsidian">
                  <Image
                    src={offMapPortrait}
                    alt="Emilie — CEO"
                    fill
                    className="object-cover object-top"
                    sizes="280px"
                  />
                </div>
                <div className="border-t border-copper/10 bg-obsidian/80 px-3 py-2">
                  <p className="font-title text-xs font-medium text-ivory">
                    Emilie
                  </p>
                  <p className="font-body text-[10px] text-titanium">
                    CEO · ALNUA
                  </p>
                </div>
              </div>
            ) : agent && status ? (
              <div
                className="flex flex-col items-center gap-1.5 px-3 py-5"
                style={{
                  boxShadow: deptColor ? `0 0 30px ${deptColor}18` : undefined,
                }}
              >
                <span className="text-4xl">{agent.icon}</span>
                <p className="font-title text-xs font-medium text-ivory">
                  {agent.name}
                </p>
                <p className="font-body text-[10px] text-titanium">
                  {agent.role}
                </p>
                <StatusPill status={status.status} />
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2 px-4 py-6">
                <span className="text-3xl">{selectedOffice.icon}</span>
                <p className="font-body text-[10px] text-titanium">
                  {selectedOffice.title}
                </p>
              </div>
            )}
          </div>

          <div className="mx-2 mt-2 shrink-0 space-y-0.5">
            {badge ? (
              <p
                className={cn(
                  "inline-block rounded px-1.5 py-0.5 font-body text-[9px]",
                  badge.highlight
                    ? "bg-copper/20 text-copper"
                    : "bg-obsidian/50 text-titanium",
                )}
              >
                {badge.label}
              </p>
            ) : null}
          </div>

          {chatMode ? (
            <div className="mx-2 mt-2 flex shrink-0 gap-1 rounded-lg bg-obsidian/60 p-0.5">
              <TabButton
                active={tab === "chat"}
                onClick={() => setTab("chat")}
                label="Chat"
              />
              <TabButton
                active={tab === "detail"}
                onClick={() => setTab("detail")}
                label="Détail"
              />
            </div>
          ) : null}

          <div className="mx-2 mt-2 min-h-0 flex-1 overflow-hidden">
            {tab === "chat" && chatMode && agent ? (
              <HqCompactChat
                key={`${selectedOffice.id}-${agent.id}`}
                mode={chatMode}
                agentFirstName={agent.name.split(" ")[0]}
                className="h-full max-h-[220px]"
              />
            ) : (
              <AgentDetailBlock status={status} agent={agent} />
            )}
          </div>

          <div className="shrink-0 space-y-1.5 p-2">
            {chatMode ? (
              <Link
                href={
                  selectedOffice.id === "secretary"
                    ? "/secretary"
                    : selectedOffice.id === "ceo"
                      ? "/ceo"
                      : "/hub"
                }
                className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-copper/15 py-1.5 font-body text-[10px] text-titanium transition hover:border-copper/30 hover:text-copper"
              >
                Ouvrir le bureau complet
                <ArrowRight className="h-3 w-3" />
              </Link>
            ) : agent ? (
              <Link
                href={openroomAgentHref(agent.id)}
                className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-copper/15 py-1.5 font-body text-[10px] text-titanium transition hover:border-copper/30 hover:text-copper"
              >
                <MessageSquare className="h-3 w-3" />
                OpenRoom
              </Link>
            ) : null}

            <button
              type="button"
              onClick={() => navigate(selectedOffice.href)}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-copper py-2 font-title text-[11px] font-medium text-obsidian transition hover:bg-copper/90"
            >
              Entrer
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      ) : (
        <div className="flex flex-1 flex-col items-center justify-center gap-3 px-5 text-center">
          <span className="text-3xl opacity-30">🏢</span>
          <p className="font-title text-sm text-ivory/80">
            Choisis un bureau
          </p>
          <p className="font-body text-[10px] leading-relaxed text-titanium/55">
            Clique sur la carte pour voir l&apos;agent, chatter avec Aria ou
            Nadia, et entrer dans le bureau.
          </p>
          <div className="mt-1 flex flex-wrap justify-center gap-2">
            <QuickLink href={ROUTES.ceo} label="CEO" />
            <QuickLink href={ROUTES.secretary} label="Nadia" />
            <QuickLink href={ROUTES.hub} label="Direction" />
            <QuickLink href={ROUTES.openroom} label="OpenRoom" />
          </div>
        </div>
      )}
    </aside>
  );
}

function TabButton({
  active,
  onClick,
  label,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex-1 rounded-md py-1 font-body text-[9px] uppercase tracking-wider transition",
        active
          ? "bg-copper/20 text-copper"
          : "text-titanium/50 hover:text-titanium",
      )}
    >
      {label}
    </button>
  );
}

function StatusPill({ status }: { status: AgentStatus["status"] }) {
  return (
    <span
      className={cn(
        "rounded-full px-2 py-0.5 font-body text-[9px] capitalize",
        status === "working"
          ? "bg-emerald-500/20 text-emerald-400"
          : status === "waiting"
            ? "bg-amber-500/20 text-amber-400"
            : status === "error"
              ? "bg-red-500/20 text-red-400"
              : "bg-titanium/10 text-titanium",
      )}
    >
      {status}
    </span>
  );
}

function AgentDetailBlock({
  status,
  agent,
}: {
  status: AgentStatus | null;
  agent: BureauAgentDef | null;
}) {
  if (!status || !agent) {
    return (
      <p className="px-1 font-body text-[10px] text-titanium/50">
        Sélectionne un agent pour voir le détail.
      </p>
    );
  }

  return (
    <div className="flex h-full max-h-[220px] flex-col gap-2 overflow-y-auto">
      {status.currentTask ? (
        <div className="rounded-lg border border-copper/10 bg-obsidian/60 p-2">
          <p className="mb-0.5 flex items-center gap-1 font-body text-[8px] uppercase tracking-wider text-titanium/45">
            <ScrollText className="h-2.5 w-2.5" />
            Tâche
          </p>
          <p className="font-body text-[10px] leading-snug text-ivory">
            {status.currentTask}
          </p>
        </div>
      ) : null}

      {status.currentFile ? (
        <div className="flex items-center gap-1.5 rounded-lg border border-copper/10 bg-obsidian/60 px-2 py-1.5 font-mono text-[9px] text-copper">
          <FileCode2 className="h-3 w-3 shrink-0" />
          <span className="truncate">{status.currentFile}</span>
        </div>
      ) : null}

      {typeof status.progress === "number" ? (
        <div>
          <div className="mb-0.5 flex justify-between font-body text-[8px] text-titanium/50">
            <span>Progression</span>
            <span>{status.progress}%</span>
          </div>
          <div className="h-1 overflow-hidden rounded-full bg-copper/10">
            <div
              className="h-full rounded-full bg-copper transition-all duration-500"
              style={{ width: `${Math.min(100, status.progress)}%` }}
            />
          </div>
        </div>
      ) : null}

      <div className="min-h-0 flex-1">
        <p className="mb-1 font-body text-[8px] uppercase tracking-wider text-titanium/45">
          Log récent
        </p>
        <div className="max-h-24 space-y-0.5 overflow-y-auto rounded border border-copper/10 bg-obsidian/50 p-1.5 font-mono text-[8px] text-titanium/55">
          {(status.log ?? []).slice(-8).map((line, i) => (
            <div key={i} className="truncate">
              {line}
            </div>
          ))}
          {!status.log?.length ? (
            <span className="text-titanium/30">Aucune activité</span>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function QuickLink({ href, label }: { href: string; label: string }) {
  return (
    <Link
      href={href}
      className="rounded-full border border-copper/20 bg-copper/5 px-2.5 py-1 font-body text-[9px] text-copper transition hover:bg-copper/15"
    >
      {label}
    </Link>
  );
}
