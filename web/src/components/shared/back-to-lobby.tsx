"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export function BackToLobby() {
  return (
    <Link
      href="/"
      className="fixed left-6 top-6 z-50 flex items-center gap-2 rounded-lg border border-copper/20 bg-obsidian-2/90 px-3 py-2 font-body text-sm text-titanium backdrop-blur-sm transition hover:border-copper/40 hover:text-ivory"
    >
      <ArrowLeft className="h-4 w-4" />
      Lobby
    </Link>
  );
}
