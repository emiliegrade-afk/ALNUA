"use client";

import { useCallback, useEffect, useState, type CSSProperties } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  HQ_HUB_ASPECT,
  HQ_HUB_IMAGE,
  HQ_HUB_IMAGE_WEBP,
  HQ_MAP_OFFICES,
  getOfficeBadge,
  getPrimaryAgentForOffice,
  type HqMapOffice,
} from "@/lib/hq-hub-offices";
import {
  prefetchAllOfficeRoutes,
  prefetchOfficeRouteOnIntent,
  warmLobbyMapCache,
} from "@/lib/hq-prefetch";
import { fetchLobbyStats, type LobbyStats } from "@/lib/lobby-api";
import { AgentAvatar } from "@/components/shared/agent-avatar";

function officeStyle(office: HqMapOffice): CSSProperties {
  return {
    left: `${office.x - office.w / 2}%`,
    top: `${office.y - office.h / 2}%`,
    width: `${office.w}%`,
    height: `${office.h}%`,
  };
}

export function HqFloorMap() {
  const router = useRouter();
  const [hoverId, setHoverId] = useState<string | null>(null);
  const [stats, setStats] = useState<LobbyStats | null>(null);

  useEffect(() => {
    warmLobbyMapCache();
    prefetchAllOfficeRoutes(router);
    void fetchLobbyStats()
      .then(setStats)
      .catch(() => setStats(null));
  }, [router]);

  const onIntent = useCallback(
    (href: string) => prefetchOfficeRouteOnIntent(router, href),
    [router],
  );

  const hovered = HQ_MAP_OFFICES.find((o) => o.id === hoverId) ?? null;
  const primary = hovered ? getPrimaryAgentForOffice(hovered) : null;

  return (
    <div className="space-y-3">
      <div
        className="relative w-full overflow-hidden rounded-xl border border-copper/25 bg-obsidian-1 shadow-[0_0_40px_-12px_rgba(224,155,106,0.35)]"
        style={{ aspectRatio: String(HQ_HUB_ASPECT) }}
      >
        <picture>
          <source srcSet={HQ_HUB_IMAGE_WEBP} type="image/webp" />
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={HQ_HUB_IMAGE}
            alt="Plan du siège ALNUA — atrium et bureaux"
            className="absolute inset-0 h-full w-full object-cover"
            draggable={false}
          />
        </picture>

        {HQ_MAP_OFFICES.map((office) => {
          const badge = stats ? getOfficeBadge(office, stats) : null;
          const active = hoverId === office.id;
          return (
            <Link
              key={office.id}
              href={office.href}
              onMouseEnter={() => setHoverId(office.id)}
              onMouseLeave={() => setHoverId(null)}
              onFocus={() => setHoverId(office.id)}
              onBlur={() => setHoverId(null)}
              onPointerDown={() => onIntent(office.href)}
              className="group absolute z-10 block rounded-md outline-none transition"
              style={officeStyle(office)}
              aria-label={`${office.title} — ${office.subtitle}`}
            >
              <span
                className={`absolute inset-0 rounded-md border transition duration-200 ${
                  active
                    ? "border-copper bg-copper/20 shadow-[0_0_20px_rgba(224,155,106,0.45)]"
                    : "border-transparent bg-transparent group-hover:border-copper/50 group-hover:bg-copper/10"
                }`}
              />
              {badge?.highlight ? (
                <span className="absolute -right-1 -top-1 z-20 rounded bg-copper px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-obsidian">
                  {badge.label}
                </span>
              ) : null}
            </Link>
          );
        })}
      </div>

      <div className="flex min-h-[64px] items-center gap-3 rounded-lg border border-copper/20 bg-obsidian-2/90 px-4 py-3">
        {hovered ? (
          <>
            {primary ? (
              <AgentAvatar agentId={primary.id} name={primary.name} size={44} ring />
            ) : (
              <span className="text-2xl">{hovered.icon}</span>
            )}
            <div className="min-w-0 flex-1">
              <p className="font-title text-sm text-ivory">
                {hovered.icon} {hovered.title}
              </p>
              <p className="truncate text-xs text-titanium/70">{hovered.subtitle}</p>
            </div>
            <Link
              href={hovered.href}
              className="shrink-0 rounded border border-copper/40 px-3 py-1.5 text-[11px] uppercase tracking-wider text-copper hover:bg-copper/10"
            >
              Entrer
            </Link>
          </>
        ) : (
          <p className="text-xs text-titanium/60">
            Survole un bureau sur le plan — clique pour y entrer. Mezzanine = Finance /
            Marketing / R&amp;D / Brand…
          </p>
        )}
      </div>
    </div>
  );
}
