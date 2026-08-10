"use client";

import { motion, useReducedMotion } from "framer-motion";
import { useConsoleData } from "./console-provider";
import { AlnuaStar } from "@/components/brand/alnua-star";
import { cn } from "@/lib/utils";

interface OrgNetworkProps {
  onSelect: (id: string) => void;
  activeId?: string | null;
}

/** Une révolution complète de la roue (lente, lisible). */
const WHEEL_SEC = 72;

/**
 * Carte org radiale — roue vivante : orbites, constellation qui tourne,
 * nœuds qui respirent, flux sur les rayons.
 */
export function OrgNetwork({ onSelect, activeId }: OrgNetworkProps) {
  const reduceMotion = useReducedMotion();
  const { departments } = useConsoleData();
  const poles = departments.filter((d) => d.id !== "ceo");
  const count = poles.length;
  const radius = 42;

  const wheelSpin = reduceMotion
    ? undefined
    : { rotate: 360 };
  const wheelTransition = reduceMotion
    ? undefined
    : { duration: WHEEL_SEC, ease: "linear" as const, repeat: Infinity };
  const counterSpin = reduceMotion ? undefined : { rotate: -360 };
  const counterTransition = wheelTransition;

  return (
    <div className="relative flex h-full min-h-0 w-full items-center justify-center">
      <div className="relative mx-auto aspect-square h-full max-h-full w-auto max-w-full org-wheel-breathe">
        {/* Anneaux décoratifs — vitesses croisées */}
        <svg
          viewBox="0 0 100 100"
          className="absolute inset-0 h-full w-full"
          fill="none"
          preserveAspectRatio="xMidYMid meet"
          aria-hidden
        >
          <g className="org-orbit-spin-fast" style={{ transformOrigin: "50px 50px" }}>
            <circle
              cx="50"
              cy="50"
              r="18"
              stroke="#E09B6A"
              strokeOpacity="0.28"
              strokeWidth="0.28"
              strokeDasharray="0.6 1.4"
              className="org-dash-crawl"
            />
          </g>
          <g className="org-orbit-spin" style={{ transformOrigin: "50px 50px" }}>
            <circle
              cx="50"
              cy="50"
              r="28"
              stroke="#B8BDC4"
              strokeOpacity="0.2"
              strokeWidth="0.22"
              strokeDasharray="1.4 2.2"
              className="org-dash-crawl-slow"
            />
            <circle
              cx="50"
              cy="50"
              r="35"
              stroke="#E09B6A"
              strokeOpacity="0.12"
              strokeWidth="0.18"
              strokeDasharray="0.4 2.8"
            />
          </g>
          <g className="org-orbit-spin-rev" style={{ transformOrigin: "50px 50px" }}>
            <circle
              cx="50"
              cy="50"
              r="42.5"
              stroke="#B8BDC4"
              strokeOpacity="0.16"
              strokeWidth="0.22"
              strokeDasharray="0.7 1.6"
              className="org-dash-crawl"
            />
          </g>

          {/* Halo respirant autour du core */}
          <circle
            cx="50"
            cy="50"
            r="12"
            stroke="#E09B6A"
            strokeOpacity="0.2"
            strokeWidth="0.15"
            className="org-halo-breathe"
            style={{ transformOrigin: "50px 50px" }}
          />
        </svg>

        {/* Roue : rayons + nœuds — rotation organique continue */}
        <motion.div
          className="absolute inset-0"
          animate={wheelSpin}
          transition={wheelTransition}
        >
          <svg
            viewBox="0 0 100 100"
            className="absolute inset-0 h-full w-full"
            fill="none"
            preserveAspectRatio="xMidYMid meet"
            aria-hidden
          >
            {poles.map((d, i) => {
              const angle = (i / count) * Math.PI * 2 - Math.PI / 2;
              const x = 50 + radius * Math.cos(angle);
              const y = 50 + radius * Math.sin(angle);
              const isActive = activeId === d.id;
              return (
                <g key={d.id}>
                  <line
                    x1="50"
                    y1="50"
                    x2={x}
                    y2={y}
                    stroke={isActive ? d.glow : "#E09B6A"}
                    strokeOpacity={isActive ? 0.8 : 0.28}
                    strokeWidth={isActive ? 0.5 : 0.26}
                    strokeDasharray="1.2 1.6"
                    className="org-link-flow"
                    style={{ animationDelay: `${i * 0.35}s` }}
                  />
                  {/* Particule qui circule sur le rayon */}
                  <circle
                    r="0.55"
                    fill={isActive ? "#F5C9A4" : "#E09B6A"}
                    fillOpacity={isActive ? 0.95 : 0.55}
                    className="org-spoke-bead"
                  >
                    <animateMotion
                      dur={`${5.5 + (i % 3) * 1.2}s`}
                      repeatCount="indefinite"
                      path={`M50,50 L${x},${y}`}
                      keyPoints="0;1"
                      keyTimes="0;1"
                      calcMode="linear"
                    />
                  </circle>
                </g>
              );
            })}
          </svg>

          {poles.map((d, i) => {
            const angle = (i / count) * Math.PI * 2 - Math.PI / 2;
            const x = 50 + radius * Math.cos(angle);
            const y = 50 + radius * Math.sin(angle);
            const Icon = d.icon;
            const isActive = activeId === d.id;
            const label = d.name.replace("Bureau ", "").replace("Pôle ", "");
            const driftDelay = i * 0.4;

            return (
              <button
                key={d.id}
                type="button"
                onClick={() => onSelect(d.id)}
                className="absolute z-20 -translate-x-1/2 -translate-y-1/2 focus:outline-none"
                style={{ left: `${x}%`, top: `${y}%` }}
                aria-label={d.name}
              >
                {/* Contre-rotation (labels/icônes droits) → dérive → respiration */}
                <motion.div animate={counterSpin} transition={counterTransition}>
                  <div
                    className="org-node-float"
                    style={{ animationDelay: `${driftDelay}s` }}
                  >
                    <motion.div
                      initial={{ opacity: 0, scale: 0.35 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{
                        duration: 0.55,
                        delay: 0.12 + i * 0.05,
                        ease: [0.22, 1, 0.36, 1],
                      }}
                      whileHover={{ scale: 1.16 }}
                      className={cn(
                        "org-node-breathe relative flex h-11 w-11 items-center justify-center border bg-void sm:h-14 sm:w-14",
                        isActive
                          ? "border-copper shadow-[0_0_22px_rgba(224,155,106,0.45)]"
                          : "border-titanium/30 hover:border-copper/55",
                      )}
                      style={{
                        animationDelay: `${i * 0.22}s`,
                        boxShadow: isActive
                          ? `0 0 22px -2px ${d.glow}`
                          : undefined,
                      }}
                    >
                      <Icon
                        className="h-[18px] w-[18px] sm:h-5 sm:w-5"
                        style={{ color: isActive ? "#F5C9A4" : "#C5CAD0" }}
                        strokeWidth={1.6}
                        aria-hidden
                      />
                      <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full border-2 border-void bg-teal org-live-dot" />
                    </motion.div>
                    <span
                      className={cn(
                        "absolute left-1/2 top-full mt-1.5 -translate-x-1/2 whitespace-nowrap text-[9px] font-medium transition-colors sm:text-[10px]",
                        isActive ? "text-metal-copper" : "text-metal-titanium",
                      )}
                    >
                      {label}
                    </span>
                  </div>
                </motion.div>
              </button>
            );
          })}
        </motion.div>

        {/* Core — point optique du X aligné sur le centre de la roue */}
        <div className="pointer-events-none absolute left-1/2 top-1/2 z-30">
          <div
            className="relative"
            style={{
              // PNG 512×592 : convergence à ~50.5% / 55.5% du cadre
              transform: "translate(-50.5%, -55.5%)",
            }}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.55 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
              className="relative"
            >
              <div className="absolute inset-0 -m-8 rounded-full bg-copper/18 blur-2xl org-core-pulse" />
              <div className="org-core-sway">
                <AlnuaStar size={52} glow animated />
              </div>
              <span className="absolute left-1/2 top-[calc(100%+6px)] -translate-x-1/2 text-[10px] uppercase tracking-[0.3em] text-metal-copper">
                Core
              </span>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}
