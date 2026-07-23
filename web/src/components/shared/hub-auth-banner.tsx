"use client";

import { useEffect, useState } from "react";
import { AlertTriangle } from "lucide-react";
import {
  checkApiHealth,
  getHubHealthCache,
  getLastKnownGoodHealth,
  subscribeHubHealth,
  type ApiHealthStatus,
} from "@/lib/hub-health";

function shouldShowError(status: ApiHealthStatus): boolean {
  if (status.online && status.authenticated) return false;
  if (getLastKnownGoodHealth() != null) return false;
  if (status.online && !status.authenticated) return true;
  return true;
}

export function HubAuthBanner() {
  const [health, setHealth] = useState<ApiHealthStatus | null>(null);
  const [confirmedError, setConfirmedError] = useState(false);

  useEffect(() => {
    const cached = getHubHealthCache() ?? getLastKnownGoodHealth();
    if (cached) {
      setHealth(cached);
      setConfirmedError(false);
    }

    let cancelled = false;

    async function verify() {
      const status = await checkApiHealth();
      if (cancelled) return;
      setHealth(status);
      setConfirmedError(shouldShowError(status));
    }

    void verify();

    const unsubscribe = subscribeHubHealth((status) => {
      if (cancelled) return;
      setHealth(status);
      if (shouldShowError(status)) {
        setConfirmedError(true);
      } else {
        setConfirmedError(false);
      }
    });

    return () => {
      cancelled = true;
      unsubscribe();
    };
  }, []);

  if (!confirmedError || !health) return null;

  if (!health.online) {
    return (
      <div className="border-b border-red-500/30 bg-red-500/10 px-6 py-2.5">
        <p className="mx-auto flex max-w-7xl items-center gap-2 font-body text-sm text-red-300">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          Backend inaccessible — lance{" "}
          <code className="rounded bg-obsidian-deep/70 px-1.5 py-0.5 text-xs">
            Demarrer-Hub.bat
          </code>
        </p>
      </div>
    );
  }

  return (
    <div className="border-b border-amber-500/30 bg-amber-500/10 px-6 py-2.5">
      <p className="mx-auto max-w-7xl font-body text-sm text-amber-200">
        <AlertTriangle className="mr-2 inline h-4 w-4 shrink-0 align-text-bottom" />
        Clé API Hub manquante côté Next.js — ajoute{" "}
        <code className="rounded bg-obsidian-deep/70 px-1.5 py-0.5 text-xs">
          HUB_API_KEY
        </code>{" "}
        dans <code className="text-xs">web/.env.local</code>, puis redémarre{" "}
        <code className="text-xs">Demarrer-Hub.bat</code>.
      </p>
    </div>
  );
}
