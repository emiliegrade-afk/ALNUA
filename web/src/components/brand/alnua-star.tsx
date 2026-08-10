"use client";

import type { CSSProperties } from "react";
import Image from "next/image";
import { cn } from "@/lib/utils";

interface AlnuaStarProps {
  size?: number;
  /** Halo cuivre autour du symbole. */
  glow?: boolean;
  /**
   * Animation « émergence » : étincelle au croisement des lames
   * (concentration des idées → produits ALNUA).
   */
  animated?: boolean;
  className?: string;
  glowColorRgb?: string;
  /** @deprecated Sans effet sur le PNG — gardé pour les appelants existants. */
  sparkMid?: string;
  sparkOuter?: string;
}

const SYMBOL_SRC = "/brand/alnua-symbol-mark.png";

/**
 * Point de convergence optique du PNG `alnua-symbol-mark.png` (512×592),
 * en % du cadre carré `object-contain` — pas le centre géométrique du box.
 */
const CORE_X = "50.5%";
const CORE_Y = "55.5%";

/**
 * Marque ALNUA — quatre lames croisées + étincelle cuivre au point de
 * convergence (charte : concentration / émergence au centre).
 */
export function AlnuaStar({
  size = 52,
  glow = false,
  animated = false,
  className,
  glowColorRgb = "224,155,106",
}: AlnuaStarProps) {
  return (
    <div
      className={cn(
        "relative inline-flex shrink-0 items-center justify-center",
        animated && "alnua-star-emergence",
        className,
      )}
      style={
        {
          width: size,
          height: size,
          ["--alnua-core-x"]: CORE_X,
          ["--alnua-core-y"]: CORE_Y,
        } as CSSProperties
      }
      role="img"
      aria-label="ALNUA"
    >
      <div
        className={cn(
          "relative h-full w-full",
          animated && "alnua-mark-breathe",
        )}
      >
        {animated ? (
          <>
            <span className="alnua-emergence-halo" aria-hidden />
            <span className="alnua-emergence-spark" aria-hidden />
          </>
        ) : null}
        <Image
          src={SYMBOL_SRC}
          alt=""
          fill
          sizes={`${size}px`}
          className="z-[2] object-contain"
          style={
            glow || animated
              ? {
                  filter: `drop-shadow(0 0 ${animated ? 14 : 10}px rgba(${glowColorRgb},${animated ? 0.75 : 0.55}))`,
                }
              : undefined
          }
        />
      </div>
    </div>
  );
}
