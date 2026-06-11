"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export function BackToLobby() {
  return (
    <Link
      href="/"
      className="fixed left-6 top-6 z-50 flex items-center gap-2 rounded-lg border border-white/10 bg-[#111827]/90 px-3 py-2 text-sm text-gray-300 backdrop-blur-sm transition hover:border-white/20 hover:text-white"
    >
      <ArrowLeft className="h-4 w-4" />
      Lobby
    </Link>
  );
}
