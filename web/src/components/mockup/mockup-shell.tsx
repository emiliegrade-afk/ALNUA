"use client";

import { useEffect, useState, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import { ConsoleProvider } from "@/components/console/console-provider";
import { ConsoleSidebar } from "@/components/console/console-sidebar";
import { MockupTopbar } from "./mockup-topbar";
import { MockupBottomBar } from "./mockup-bottom-bar";
import { cn } from "@/lib/utils";

interface MockupShellProps {
  children: ReactNode;
  rightSidebar?: ReactNode;
  hideFooter?: boolean;
}

export function MockupShell({ children, rightSidebar, hideFooter }: MockupShellProps) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMobileOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <ConsoleProvider>
      <div className="flex h-[100dvh] w-full overflow-hidden bg-obsidian">
        <ConsoleSidebar
          mobileOpen={mobileOpen}
          onMobileClose={() => setMobileOpen(false)}
        />

        <div className="flex min-w-0 flex-1 flex-col">
          <MockupTopbar onMobileMenu={() => setMobileOpen(true)} />

          <div className="flex flex-1 overflow-hidden">
            <main
              id="alnua-workspace"
              className={cn(
                "alnua-scroll relative flex-1 overflow-y-auto",
                rightSidebar ? "min-w-0" : "w-full",
              )}
            >
              <div className="pointer-events-none absolute inset-0 bg-grid-bronze opacity-[0.15]" />
              <div className="relative flex min-h-full flex-col p-4 sm:p-5 lg:p-6">
                <div key={pathname} className="flex-1">
                  {children}
                </div>

                {!hideFooter ? (
                  <footer className="relative mt-8 flex flex-col items-center justify-between gap-2 border-t border-bronze-faint pt-5 sm:flex-row">
                    <p className="text-[10px] text-titane/40">
                      © {new Date().getFullYear()} ALNUA — Virtual AI Enterprise
                    </p>
                    <p className="text-[10px] tracking-wide text-titane/35">
                      Technology should serve humanity. Not the opposite.
                    </p>
                  </footer>
                ) : null}
              </div>
            </main>

            {rightSidebar ? (
              <aside className="alnua-scroll hidden w-[300px] shrink-0 overflow-y-auto border-l border-bronze-faint bg-obsidian-deep/50 px-4 py-5 lg:block">
                {rightSidebar}
              </aside>
            ) : null}
          </div>

          <MockupBottomBar />
        </div>
      </div>
    </ConsoleProvider>
  );
}
