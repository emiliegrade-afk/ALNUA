"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { useHubNavigate } from "@/components/layout/hub-navigation";
import { prefetchLobby } from "@/lib/hq-prefetch";

interface BackToLobbyProps {
  className?: string;
}

export function BackToLobby({ className }: BackToLobbyProps) {
  const router = useRouter();
  const { navigate } = useHubNavigate();

  useEffect(() => {
    prefetchLobby(router);
  }, [router]);

  return (
    <button
      type="button"
      onClick={() => navigate("/")}
      className={
        className ??
        "mb-4 inline-flex items-center gap-1.5 rounded-lg border border-bronze-faint bg-obsidian/70 px-2.5 py-1.5 text-[11px] font-medium uppercase tracking-[0.12em] text-titane/70 transition hover:border-bronze/40 hover:text-ivoire"
      }
    >
      <ArrowLeft className="h-3.5 w-3.5" />
      Lobby
    </button>
  );
}
