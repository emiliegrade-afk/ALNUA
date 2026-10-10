"use client";

import { useEffect, useState, type ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { ConsoleProvider } from "./console-provider";
import {
  DeptV2Sidebar,
  DeptV2CommandBar,
  DeptV2Header,
} from "@/components/dept-v2";
import { CONSOLE_POLES } from "@/lib/console/departments";
import {
  CONSOLE_ACTIVITY,
  CONSOLE_AGENTS,
  CONSOLE_HOME,
} from "@/lib/console/nav";
import { ROUTES } from "@/lib/routes";
import { useCooStore } from "@/store/coo-store";
import { useQuickCaptureStore } from "@/store/quick-capture-store";
import { cn } from "@/lib/utils";

const SIDEBAR_KEY = "alnua.dept-sidebar-collapsed";

interface ConsoleShellProps {
  children: ReactNode;
}

function activeDeptFromPath(pathname: string): string {
  if (pathname === "/live" || pathname.startsWith("/live/")) return "secretary";
  const pole = CONSOLE_POLES.find(
    (p) => pathname === p.href || pathname.startsWith(`${p.href}/`),
  );
  return pole?.id ?? "hub";
}

/**
 * Shell Command Center — même chrome que les pages *-v2 :
 * en-tête marque ALNUA + colonne départements rabattable + barre cmd.
 */
export function ConsoleShell({ children }: ConsoleShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    try {
      setCollapsed(localStorage.getItem(SIDEBAR_KEY) === "1");
    } catch {
      /* ignore */
    }
  }, []);

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

  function handleCollapsedChange(next: boolean) {
    setCollapsed(next);
    try {
      localStorage.setItem(SIDEBAR_KEY, next ? "1" : "0");
    } catch {
      /* ignore */
    }
  }

  const openDrawer = useCooStore((s) => s.openDrawer);
  const setCaptureOpen = useQuickCaptureStore((s) => s.setOpen);

  const viewKey =
    pathname === CONSOLE_HOME
      ? "dashboard"
      : pathname === CONSOLE_AGENTS
        ? "agents"
        : pathname === CONSOLE_ACTIVITY
          ? "activity"
          : pathname;

  const headerTab =
    pathname === ROUTES.analytics
      ? ("analytics" as const)
      : pathname === ROUTES.tickets
        ? ("missions" as const)
        : pathname === ROUTES.library
          ? ("resources" as const)
          : ("overview" as const);

  return (
    <ConsoleProvider>
      <div className="dept-void-shell flex h-[100dvh] w-full flex-col overflow-hidden bg-void font-sans text-ivoire">
        <DeptV2Header
          deptHref={ROUTES.app}
          activeTab={headerTab}
          onMobileMenu={() => setMobileOpen(true)}
        />

        <div className="flex min-h-0 flex-1">
          {mobileOpen ? (
            <div
              className="fixed inset-0 z-40 bg-void/80 backdrop-blur-sm lg:hidden"
              onClick={() => setMobileOpen(false)}
              aria-hidden
            />
          ) : null}

          <div
            className={cn(
              "fixed bottom-0 top-[clamp(56px,6vh,64px)] z-50 flex lg:static lg:z-auto lg:top-auto",
              mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
              "transition-transform duration-300",
            )}
          >
            <DeptV2Sidebar
              activeDeptId={activeDeptFromPath(pathname)}
              coreSubtitle="Command Center"
              collapsed={collapsed}
              onCollapsedChange={handleCollapsedChange}
            />
          </div>

          <div className="dept-hud flex min-w-0 flex-1 flex-col">
            <main
              id="alnua-workspace"
              className="alnua-scroll relative flex-1 overflow-y-auto"
            >
              <div className="relative flex min-h-full flex-col gap-4 px-5 pb-4 pt-4 sm:px-8">
                <div key={viewKey} className="flex-1">
                  {children}
                </div>

                <DeptV2CommandBar
                  actions={[
                    {
                      icon: "✦",
                      label: "Nouvelle mission",
                      onClick: () => setCaptureOpen(true),
                    },
                    {
                      icon: "〰",
                      label: "Rapport d'équipe",
                      onClick: () => router.push(ROUTES.activity),
                    },
                    {
                      icon: "◎",
                      label: "Assistant Aria",
                      onClick: openDrawer,
                    },
                    {
                      icon: "⚙",
                      label: "Paramètres",
                      onClick: () => router.push(ROUTES.settings),
                    },
                  ]}
                />

                <footer className="relative flex flex-col items-center justify-between gap-2 border-t border-titanium/20 pt-4 sm:flex-row">
                  <p className="text-[11px] text-metal-titanium opacity-70">
                    © {new Date().getFullYear()} ALNUA — Virtual AI Enterprise ·
                    Console Hub
                  </p>
                  <p className="text-[11px] tracking-wide text-metal-titanium opacity-55">
                    Technology should serve humanity. Not the opposite.
                  </p>
                </footer>
              </div>
            </main>
          </div>
        </div>
      </div>
    </ConsoleProvider>
  );
}
