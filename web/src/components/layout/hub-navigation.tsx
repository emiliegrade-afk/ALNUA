"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  useTransition,
  type ReactNode,
} from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  prefetchOfficeRoute,
  warmLobbyMapCache,
} from "@/lib/hq-prefetch";
import { cn } from "@/lib/utils";

interface HubNavigationContextValue {
  navigate: (href: string) => void;
  isNavigating: boolean;
}

const HubNavigationContext = createContext<HubNavigationContextValue | null>(
  null,
);

function NavigationProgress({ active }: { active: boolean }) {
  return (
    <div
      aria-hidden
      className={cn(
        "pointer-events-none fixed inset-x-0 top-0 z-[100] h-0.5 overflow-hidden transition-opacity duration-200",
        active ? "opacity-100" : "opacity-0",
      )}
    >
      <div
        className={cn(
          "h-full w-1/3 bg-gradient-to-r from-transparent via-copper to-transparent",
          active && "animate-hub-nav-progress",
        )}
      />
    </div>
  );
}

export function HubNavigationProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isPending, startTransition] = useTransition();
  const [target, setTarget] = useState<string | null>(null);

  useEffect(() => {
    setTarget(null);
  }, [pathname]);

  const navigate = useCallback(
    (href: string) => {
      if (!href || href === pathname) return;
      prefetchOfficeRoute(router, href);
      if (href === "/") warmLobbyMapCache();
      setTarget(href);
      startTransition(() => {
        router.prefetch(href);
        router.push(href);
      });
    },
    [pathname, router, startTransition],
  );

  const isNavigating = isPending || target !== null;

  return (
    <HubNavigationContext.Provider value={{ navigate, isNavigating }}>
      <NavigationProgress active={isNavigating} />
      {isNavigating ? (
        <div
          aria-hidden
          className="pointer-events-none fixed inset-0 z-[90] bg-obsidian/15 backdrop-blur-[1px] transition-opacity duration-150"
        />
      ) : null}
      {children}
    </HubNavigationContext.Provider>
  );
}

/** Fluid lobby ↔ bureau navigation with instant progress feedback. */
export function useHubNavigate(): HubNavigationContextValue {
  const ctx = useContext(HubNavigationContext);
  const router = useRouter();
  if (ctx) return ctx;
  return {
    navigate: (href: string) => router.push(href),
    isNavigating: false,
  };
}
