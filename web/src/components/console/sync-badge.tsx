"use client";

import { useConsoleData } from "./console-provider";

/** Badge synchronisation — toutes les cartes partagent le même tick. */
export function SyncBadge({ className }: { className?: string }) {
  const { lastSyncedAt, pollIntervalMs } = useConsoleData();
  const label = lastSyncedAt
    ? lastSyncedAt.toLocaleTimeString("fr-FR", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      })
    : "…";

  return (
    <span
      className={className}
      title={`Rafraîchissement auto toutes les ${pollIntervalMs / 1000}s`}
    >
      sync {label}
    </span>
  );
}
