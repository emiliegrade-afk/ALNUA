"use client";

import { useEffect } from "react";

import { openLiveStream } from "@/lib/live-api";
import { useLiveStore } from "@/store/live-store";

/** Keeps the live store in sync with the Hub task stream while mounted. */
export function useLiveStream(): void {
  useEffect(() => {
    const { upsert, setConnection } = useLiveStore.getState();
    setConnection("connecting");
    // EventSource reconnects by itself; we only mirror its state in the UI.
    return openLiveStream({
      onTask: upsert,
      onOpen: () => setConnection("online"),
      onError: () => setConnection("reconnecting"),
    });
  }, []);
}
