"use client";

import { X } from "lucide-react";
import { AgentOfficeAvatar } from "./agent-office-avatar";
import { AgentWorkingAnimation } from "./agent-working-animation";
import { getAgentOfficeAssets } from "@/lib/agent-assets";
import type { AgentStatus } from "@/lib/openroom-api";
import { cn } from "@/lib/utils";

interface AgentFocusPanelProps {
  agent: { id: string; name: string; emoji: string; role: string; branch?: import("@/lib/dept-colors").DeptKey };
  status: AgentStatus;
  onClose: () => void;
}

export function AgentFocusPanel({
  agent,
  status,
  onClose,
}: AgentFocusPanelProps) {
  const officeAssets = getAgentOfficeAssets(agent.id);

  return (
    <>
      <div
        className="fixed inset-0 z-40 bg-obsidian-deep/70"
        onClick={onClose}
        aria-hidden
      />
      <div className="fixed bottom-0 right-0 top-0 z-50 w-96 border-l border-[#C08A62]/20 bg-[#0E1014] shadow-[-8px_0_40px_rgba(0,0,0,0.6)]">
        <div className="flex items-center justify-between border-b border-copper/15 px-5 py-4">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{agent.emoji}</span>
            <div>
              <h3 className="font-title font-medium text-ivory">{agent.name}</h3>
              <p className="text-xs text-titanium">{agent.role}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-titanium transition-colors hover:text-ivory"
            aria-label="Fermer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="h-[calc(100vh-72px)] space-y-4 overflow-y-auto p-5">
          {officeAssets ? (
            <AgentOfficeAvatar
              agentId={agent.id}
              name={agent.name}
              role={agent.role}
              branch={agent.branch ?? "hub"}
              status={status.status}
              currentTask={status.currentTask}
              variant="compact"
            />
          ) : null}

          <div className="flex items-center gap-2">
            <span
              className={cn(
                "h-2 w-2 rounded-full",
                status.status === "working"
                  ? "animate-pulse bg-copper"
                  : status.status === "waiting"
                    ? "animate-pulse bg-titanium/60"
                    : status.status === "error"
                      ? "bg-red-500"
                      : "bg-titanium/20",
              )}
            />
            <span className="text-sm capitalize text-titanium">
              {status.status === "working"
                ? "En train de coder..."
                : status.status === "waiting"
                  ? "En attente..."
                  : status.status === "error"
                    ? "Erreur"
                    : "Inactif"}
            </span>
          </div>

          {!officeAssets ? (
            <AgentWorkingAnimation
              status={status.status}
              currentCodeLines={status.recentCode}
            />
          ) : null}

          {status.currentTask ? (
            <div className="rounded-lg border border-copper/10 bg-[#16191F] p-3">
              <p className="mb-1 text-[10px] uppercase tracking-widest text-titanium/50">
                Tâche
              </p>
              <p className="text-sm text-ivory">{status.currentTask}</p>
            </div>
          ) : null}

          {status.currentFile ? (
            <div className="rounded-lg border border-copper/10 bg-[#16191F] p-3 font-mono text-xs text-copper">
              📄 {status.currentFile}
            </div>
          ) : null}

          {status.status === "working" &&
          typeof status.progress === "number" ? (
            <div>
              <div className="mb-1 flex justify-between text-xs text-titanium">
                <span>Progression</span>
                <span>{status.progress}%</span>
              </div>
              <div className="h-1.5 rounded-full bg-obsidian-3">
                <div
                  className="h-full rounded-full bg-copper transition-all duration-500"
                  style={{ width: `${status.progress}%` }}
                />
              </div>
            </div>
          ) : null}

          <div>
            <p className="mb-2 text-[10px] uppercase tracking-widest text-titanium/50">
              Log récent
            </p>
            <div className="max-h-48 space-y-1 overflow-y-auto rounded bg-[#16191F] p-3 font-mono text-[10px] text-titanium/60">
              {(status.log ?? []).slice(-10).map((line, i) => (
                <div key={i}>{line}</div>
              ))}
              {!status.log || status.log.length === 0 ? (
                <span className="text-titanium/30">
                  Aucune activité récente
                </span>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
