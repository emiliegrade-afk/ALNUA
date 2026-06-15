"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { useHubNavigate } from "@/components/layout/hub-navigation";
import { prefetchLobby } from "@/lib/hq-prefetch";

export function BackToLobby() {
  const router = useRouter();
  const { navigate } = useHubNavigate();

  useEffect(() => {
    prefetchLobby(router);
  }, [router]);

  return (
    <button
      type="button"
      onClick={() => navigate("/")}
      className="fixed left-6 top-6 z-50 flex items-center gap-2 rounded-lg border border-copper/20 bg-obsidian-2/90 px-3 py-2 font-body text-sm text-titanium backdrop-blur-sm transition hover:border-copper/40 hover:text-ivory"
    >
      <ArrowLeft className="h-4 w-4" />
      Lobby
    </button>
  );
}
