"use client";

import { useEffect, useState, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import { ConsoleProvider } from "./console-provider";
import { ConsoleSidebar } from "./console-sidebar";
import { ConsoleTopbar } from "./console-topbar";
import { CONSOLE_ACTIVITY, CONSOLE_AGENTS, CONSOLE_HOME } from "@/lib/console/nav";

interface ConsoleShellProps {
  children: ReactNode;
}

export function ConsoleShell({ children }: ConsoleShellProps) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const el = document.getElementById("alnua-workspace");
    if (el) el.scrollTo({ top: 0, behavior: "auto" });
  }, [pathname]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMobileOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const viewKey =
    pathname === CONSOLE_HOME
      ? "dashboard"
      : pathname === CONSOLE_AGENTS
        ? "agents"
        : pathname === CONSOLE_ACTIVITY
          ? "activity"
          : pathname;

  return (
    <ConsoleProvider>
      <div className="flex h-[100dvh] w-full overflow-hidden bg-obsidian">
        <ConsoleSidebar
          mobileOpen={mobileOpen}
          onMobileClose={() => setMobileOpen(false)}
        />

        <div className="flex min-w-0 flex-1 flex-col">
          <ConsoleTopbar onMobileMenu={() => setMobileOpen(true)} />

          <main
            id="alnua-workspace"
            className="alnua-scroll relative flex-1 overflow-y-auto"
          >
            <div className="pointer-events-none absolute inset-0 bg-grid-bronze opacity-[0.15]" />
            <div className="relative flex min-h-full flex-col p-4 sm:p-6 lg:p-8">
              <div key={viewKey} className="flex-1">
                {children}
              </div>

              <footer className="relative mt-10 flex flex-col items-center justify-between gap-2 border-t border-bronze-faint pt-6 sm:flex-row">
                <p className="text-[11px] text-titane/45">
                  © {new Date().getFullYear()} ALNUA — Virtual AI Enterprise ·
                  Console Hub
                </p>
                <p className="text-[11px] tracking-wide text-titane/40">
                  Technology should serve humanity. Not the opposite.
                </p>
              </footer>
            </div>
          </main>
        </div>
      </div>
    </ConsoleProvider>
  );
}
