"use client";

import { AgentAvatar } from "./agent-avatar";
import { AgentOfficeAvatar } from "./agent-office-avatar";
import { getAgentOfficeAssets } from "@/lib/agent-assets";
import type { DeptKey } from "@/lib/dept-colors";
import type { AgentStatusKind } from "@/lib/openroom-api";

export interface OpenRoomAgentTileProps {
  id: string;
  name: string;
  role: string;
  emoji: string;
  branch: DeptKey;
  status: AgentStatusKind;
  currentTask?: string;
  onClick?: () => void;
}

/** OpenRoom tile — portrait animé si assets bureau, sinon emoji legacy. */
export function OpenRoomAgentTile({
  id,
  name,
  role,
  emoji,
  branch,
  status,
  currentTask,
  onClick,
}: OpenRoomAgentTileProps) {
  if (getAgentOfficeAssets(id)) {
    return (
      <AgentOfficeAvatar
        agentId={id}
        name={name}
        role={role}
        branch={branch}
        status={status}
        currentTask={currentTask}
        onClick={onClick}
        variant="tile"
      />
    );
  }

  return (
    <AgentAvatar
      name={name}
      role={role}
      emoji={emoji}
      branch={branch}
      status={status}
      currentTask={currentTask}
      onClick={onClick}
    />
  );
}
