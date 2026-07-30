"use client";

import { useId } from "react";
import { cn } from "@/lib/utils";

interface AlnuaStarProps {
  size?: number;
  /** Halo lumineux autour de la marque (cœur du widget CORE, orbe de la barre
   * d'action). */
  glow?: boolean;
  /** Pulsation lente de l'étincelle — coupée quand le système n'est pas
   * opérationnel. */
  animated?: boolean;
  className?: string;
  /** Teintes de l'étincelle — par défaut la charte de marque officielle
   * (cuivre rosé #C08A72). La page de référence /app-v2 les surcharge avec
   * les valeurs exactes de la maquette source (#C87F4E) pour un calque
   * fidèle au pixel ; le reste du Hub garde la charte par défaut. */
  sparkMid?: string;
  sparkOuter?: string;
  glowColorRgb?: string;
}

/**
 * Marque ALNUA en vectoriel — le X de la charte : quatre lames effilées
 * croisées en métal (titane → ivoire) et l'étincelle cuivre rosé au point de
 * convergence.
 *
 * Pourquoi pas le PNG `/brand/alnua-mark.png` ici : ce fichier est matricé sur
 * un fond noir opaque, ce qui pose un carré sombre visible dès qu'on le
 * superpose à un dégradé (constaté dans le widget CORE et l'orbe de la barre
 * d'action). Le vectoriel se pose proprement sur n'importe quel fond et reste
 * net à toute taille. `AlnuaLogo` (le PNG) reste utilisé là où la marque est
 * posée sur un aplat sombre uni.
 */
export function AlnuaStar({
  size = 52,
  glow = false,
  animated = true,
  className,
  sparkMid = "#D9A88F",
  sparkOuter = "#C08A72",
  glowColorRgb = "192,138,114",
}: AlnuaStarProps) {
  // `useId` plutôt que des identifiants fixes : plusieurs marques coexistent
  // sur la même page (sidebar, barre d'action) et deux <defs> de même id se
  // télescopent.
  const uid = useId().replace(/:/g, "");
  const blade = `blade-${uid}`;
  const bladeDim = `bladeDim-${uid}`;
  const spark = `spark-${uid}`;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      role="img"
      aria-label="ALNUA"
      className={cn(className)}
      style={glow ? { filter: `drop-shadow(0 0 10px rgba(${glowColorRgb},.55))` } : undefined}
    >
      <defs>
        {/* Face éclairée des lames — titane poli vers l'ivoire. */}
        <linearGradient id={blade} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#F5F2EA" />
          <stop offset="45%" stopColor="#C9CDD3" />
          <stop offset="100%" stopColor="#A7ADB5" />
        </linearGradient>
        {/* Face à l'ombre — donne le relief biseauté du logo. */}
        <linearGradient id={bladeDim} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#8B9199" />
          <stop offset="100%" stopColor="#5C6167" />
        </linearGradient>
        <radialGradient id={spark}>
          <stop offset="0%" stopColor="#FFF3EA" />
          <stop offset="35%" stopColor={sparkMid} />
          <stop offset="70%" stopColor={sparkOuter} stopOpacity=".55" />
          <stop offset="100%" stopColor={sparkOuter} stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* Quatre lames effilées convergeant au centre. Chaque lame est un
          quadrilatère fin : pointe à l'extérieur, base étroite au centre. */}
      <g>
        <polygon points="14,4 50,46 46,52 8,16" fill={`url(#${blade})`} />
        <polygon points="86,4 54,46 58,52 92,16" fill={`url(#${bladeDim})`} />
        <polygon points="8,84 46,48 50,54 14,96" fill={`url(#${bladeDim})`} />
        <polygon points="92,84 54,48 50,54 86,96" fill={`url(#${blade})`} />
      </g>

      {/* Étincelle cuivre au point de convergence. */}
      <circle
        cx="50"
        cy="50"
        r="22"
        fill={`url(#${spark})`}
        className={cn(animated && "animate-alnua-pulse")}
      />
      <circle cx="50" cy="50" r="2.6" fill="#FFF3EA" />
    </svg>
  );
}
