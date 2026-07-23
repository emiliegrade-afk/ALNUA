"use client";

import { useEffect, useRef, useState } from "react";
import {
  getHubHealthCache,
  getLastKnownGoodHealth,
  HUB_HEALTH_POLL_DOWN_MS,
  HUB_HEALTH_POLL_OK_MS,
  probeHubApiLive,
  publishHubHealthStatus,
  subscribeHubHealth,
  type ApiHealthStatus,
} from "@/lib/hub-health";

export type HubHealthPhase = "checking" | "ok" | "key" | "down";

export function hubHealthPhase(status: ApiHealthStatus | null): HubHealthPhase {
  if (!status) return "checking";
  if (!status.online) return "down";
  if (!status.authenticated) return "key";
  return "ok";
}

export function useHubHealthLive(): {
  status: ApiHealthStatus | null;
  phase: HubHealthPhase;
  lastCheckedAt: number | null;
  refresh: () => void;
} {
  // Never read sessionStorage during initial render — SSR and client must match.
  const [status, setStatus] = useState<ApiHealthStatus | null>(null);
  const [lastCheckedAt, setLastCheckedAt] = useState<number | null>(null);
  const [tick, setTick] = useState(0);
  const failStreakRef = useRef(0);
  const [displayStatus, setDisplayStatus] = useState<ApiHealthStatus | null>(null);

  useEffect(() => {
    const cached = getHubHealthCache() ?? getLastKnownGoodHealth();
    if (cached) {
      setStatus(cached);
      setDisplayStatus(cached);
    }
  }, []);

  useEffect(() => {
    if (!status) {
      setDisplayStatus(null);
      return;
    }
    if (status.online && status.authenticated) {
      failStreakRef.current = 0;
      setDisplayStatus(status);
      return;
    }
    failStreakRef.current += 1;
    if (failStreakRef.current >= 8) {
      setDisplayStatus(status);
    }
  }, [status]);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;

    async function runProbe() {
      const result = await probeHubApiLive(12_000);
      if (cancelled) return;
      setStatus(result);
      setLastCheckedAt(Date.now());
      publishHubHealthStatus(result);
      const delay =
        result.online && result.authenticated
          ? HUB_HEALTH_POLL_OK_MS
          : HUB_HEALTH_POLL_DOWN_MS;
      timer = setTimeout(runProbe, delay);
    }

    void runProbe();

    const unsubscribe = subscribeHubHealth((next) => {
      if (cancelled) return;
      setStatus(next);
      setLastCheckedAt(Date.now());
    });

    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
      unsubscribe();
    };
  }, [tick]);

  return {
    status: displayStatus,
    phase: hubHealthPhase(displayStatus),
    lastCheckedAt,
    refresh: () => setTick((n) => n + 1),
  };
}
