"use client";

import { useEffect, useState } from "react";
import { useOptionalConsoleData } from "@/components/console/console-provider";
import { fetchAgentsStatus, type AgentStatus } from "@/lib/openroom-api";

const FALLBACK_POLL_MS = 12_000;

/**
 * Shared agent status source — reuses ConsoleProvider polling when inside
 * the bureau shell, otherwise falls back to a local poll.
 */
export function useAgentStatuses(): Record<string, AgentStatus> {
  const consoleData = useOptionalConsoleData();
  const [localStatuses, setLocalStatuses] = useState<Record<string, AgentStatus>>({});

  useEffect(() => {
    if (consoleData) return;

    let cancelled = false;
    let intervalId: ReturnType<typeof setInterval> | undefined;

    async function poll() {
      const result = await fetchAgentsStatus();
      if (cancelled) return;
      setLocalStatuses(result.data.agents);
    }

    const start = () => {
      void poll();
      intervalId = setInterval(() => void poll(), FALLBACK_POLL_MS);
    };

    if (typeof requestIdleCallback !== "undefined") {
      const idleId = requestIdleCallback(start, { timeout: 600 });
      return () => {
        cancelled = true;
        cancelIdleCallback(idleId);
        if (intervalId) clearInterval(intervalId);
      };
    }

    const timeoutId = setTimeout(start, 0);
    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
      if (intervalId) clearInterval(intervalId);
    };
  }, [consoleData]);

  return consoleData?.liveAgents ?? localStatuses;
}
