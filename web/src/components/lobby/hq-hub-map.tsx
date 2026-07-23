"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useHubNavigate } from "@/components/layout/hub-navigation";
import type { LobbyStats } from "@/lib/lobby-api";
import {
  HQ_HUB_ASPECT,
  HQ_HUB_IMAGE,
  HQ_HUB_IMAGE_WEBP,
  HQ_MAP_OFFICES,
  getOfficeBadge,
  type HqMapOffice,
} from "@/lib/hq-hub-offices";
import { prefetchOfficeRoute } from "@/lib/hq-prefetch";
import { cn } from "@/lib/utils";

const IMAGE_WIDTH = 1536;
const IMAGE_HEIGHT = 1024;
const IMAGE_ASPECT = HQ_HUB_ASPECT;

interface HqHubMapProps {
  stats: LobbyStats;
  selectedOfficeId: string | null;
  onSelectOffice: (office: HqMapOffice) => void;
}

/** Scale down to fit — never crop top or bottom. */
function fitContain(availW: number, availH: number) {
  if (availW <= 0 || availH <= 0) return { width: 0, height: 0 };
  if (availW / availH > IMAGE_ASPECT) {
    const height = Math.floor(availH);
    return { width: Math.floor(height * IMAGE_ASPECT), height };
  }
  const width = Math.floor(availW);
  return { width, height: Math.floor(width / IMAGE_ASPECT) };
}

export function HqHubMap({
  stats,
  selectedOfficeId,
  onSelectOffice,
}: HqHubMapProps) {
  const router = useRouter();
  const { navigate } = useHubNavigate();
  const searchParams = useSearchParams();
  const debugHotspots = searchParams.get("hotspots") === "1";
  const containerRef = useRef<HTMLDivElement>(null);
  const [frame, setFrame] = useState({ width: 0, height: 0 });
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const hovered = HQ_MAP_OFFICES.find((o) => o.id === hoveredId) ?? null;

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const measure = () => {
      const rect = el.getBoundingClientRect();
      let width = Math.floor(rect.width);
      let height = Math.floor(rect.height);

      // Cursor Simple Browser / embedded WebViews can report 0 height briefly.
      if (height <= 0) {
        height = Math.max(
          Math.floor(window.innerHeight - 36),
          Math.floor(document.documentElement.clientHeight - 36),
          480,
        );
      }
      if (width <= 0) {
        width = Math.max(
          Math.floor(window.innerWidth),
          Math.floor(document.documentElement.clientWidth),
          320,
        );
      }

      setFrame(fitContain(width, height));
    };

    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    window.addEventListener("resize", measure);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, []);

  const handleEnter = useCallback(
    (office: HqMapOffice) => navigate(office.href),
    [navigate],
  );

  const handleHoverOffice = useCallback(
    (office: HqMapOffice) => {
      setHoveredId(office.id);
      prefetchOfficeRoute(router, office.href);
    },
    [router],
  );

  const handleIntentOffice = useCallback(
    (office: HqMapOffice) => {
      prefetchOfficeRoute(router, office.href);
    },
    [router],
  );

  return (
    <div
      ref={containerRef}
      className="absolute inset-x-0 top-0 bottom-9 flex items-center justify-center bg-obsidian"
    >
      {frame.width > 0 && frame.height > 0 ? (
        <div
          className="relative shrink-0"
          style={{ width: frame.width, height: frame.height }}
        >
          <picture>
            <source srcSet={HQ_HUB_IMAGE_WEBP} type="image/webp" />
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={HQ_HUB_IMAGE}
              alt="Siège social ALNUA — 15 zones"
              width={IMAGE_WIDTH}
              height={IMAGE_HEIGHT}
              fetchPriority="high"
              decoding="async"
              className="block h-full w-full select-none"
              draggable={false}
            />
          </picture>

          {HQ_MAP_OFFICES.map((office) => {
            const isHot =
              hoveredId === office.id || selectedOfficeId === office.id;

            return (
              <button
                key={office.id}
                type="button"
                aria-label={`Sélectionner — ${office.title}`}
                aria-pressed={selectedOfficeId === office.id}
                className={cn(
                  "absolute z-10 cursor-pointer rounded-md border transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-copper/60",
                  debugHotspots
                    ? "border-copper/70 bg-copper/20"
                    : isHot
                      ? "border-copper/60 bg-copper/12 shadow-[0_0_20px_rgba(192,138,98,0.25)]"
                      : "border-transparent bg-transparent hover:border-copper/30 hover:bg-copper/6",
                )}
                style={{
                  left: `${office.x - office.w / 2}%`,
                  top: `${office.y - office.h / 2}%`,
                  width: `${office.w}%`,
                  height: `${office.h}%`,
                }}
                onMouseEnter={() => handleHoverOffice(office)}
                onMouseLeave={() => setHoveredId(null)}
                onPointerDown={() => handleIntentOffice(office)}
                onClick={() => {
                  if (selectedOfficeId === office.id) {
                    handleEnter(office);
                    return;
                  }
                  onSelectOffice(office);
                  prefetchOfficeRoute(router, office.href);
                }}
                onDoubleClick={() => handleEnter(office)}
              >
                {debugHotspots ? (
                  <span className="pointer-events-none absolute left-0 top-0 bg-obsidian/80 px-0.5 font-mono text-[8px] text-copper">
                    {office.number || "·"} {office.shortcutLabel}
                  </span>
                ) : null}
              </button>
            );
          })}
        </div>
      ) : (
        <p className="font-body text-sm text-titanium/60">Chargement du siège social…</p>
      )}

      <AnimatePresence>
        {hovered ? (
          <motion.div
            key={hovered.id}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 4 }}
            className="pointer-events-none absolute bottom-12 right-3 z-40 rounded-md border border-copper/20 bg-obsidian/80 px-3 py-1.5 backdrop-blur-md"
          >
            <p className="font-title text-xs font-medium text-ivory">
              {hovered.title}
            </p>
            <p className="font-body text-[10px] text-titanium">
              {getOfficeBadge(hovered, stats).label} ·{" "}
              {selectedOfficeId === hovered.id
                ? "re-clic ou Entrée pour entrer"
                : "clic pour sélectionner"}
            </p>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}
