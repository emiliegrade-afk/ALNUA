"use client";

import Image from "next/image";
import { cn } from "@/lib/utils";

interface AlnuaStarProps {
  size?: number;
  /** Halo lumineux autour de la marque (cœur du widget CORE, orbe de la barre
   * d'action). Toujours statique — voir note sur `animated`. */
  glow?: boolean;
  /** Ancien effet de pulsation, désactivé : le keyframe partagé
   * `animate-alnua-glow` (globals.css) anime le flou du `drop-shadow`, or ce
   * flou grossit surtout la zone déjà quasi opaque de l'étincelle du PNG
   * (contrairement à l'ancien SVG où l'étincelle n'était qu'un dégradé peu
   * opaque) — résultat : une tache floue qui pulse au centre du symbole au
   * lieu d'un simple liseré lumineux. Prop gardée (no-op) pour ne pas casser
   * les appelants (`animated={healthy}` sur le widget CORE, etc.).
   * [À COMPLÉTER : réintroduire une pulsation propre nécessiterait un halo
   * séparé, positionné indépendamment du PNG — pas fait ici faute de repère
   * fiable sur l'étincelle réelle du PNG, cf. tentative ratée précédente]. */
  animated?: boolean;
  className?: string;
  /** Couleur du halo (`drop-shadow`) quand `glow` est actif. */
  glowColorRgb?: string;
  /** @deprecated Sans effet — l'étincelle est gravée dans `alnua-symbol-mark.png`,
   * ces props ne recolorent pas un pixel du PNG. Gardées pour ne pas casser
   * les appelants existants (plusieurs pages /*-v2 les passent encore). */
  sparkMid?: string;
  sparkOuter?: string;
}

// Le PNG (512x592) est légèrement plus haut que large — le symbole officiel
// mesuré sur `assets/brand/aluna-brand-board.png` (panneau « LE SYMBOLE »)
// donne ~1.17, cohérent avec les 2 autres déclinaisons DA (construction et
// app icon). `object-contain` (ci-dessous) gère cet écart sans distorsion.
const SYMBOL_SRC = "/brand/alnua-symbol-mark.png";

/**
 * Marque ALNUA — le symbole officiel de la charte : quatre lames effilées
 * croisées en métal (titane → ivoire), les deux chevrons fins qui les
 * flanquent, et l'étincelle cuivre rosé au point de convergence.
 *
 * Rendu en PNG alpha (`alnua-symbol-mark.png`, extrait et matricé à partir de
 * `assets/brand/aluna-brand-board.png` — la vraie référence DA, pas une
 * reconstruction à la main) plutôt qu'en SVG vectoriel : deux tentatives de
 * revectorisation à la main (lames simples, puis lames + chevrons
 * approximés) ont chacune fini par diverger visiblement de la charte — cf.
 * historique git de ce fichier. Le PNG élimine ce risque : c'est littéralement
 * l'image de la charte, juste détourée (alpha basé sur la luminance, seuil
 * réglé pour ne laisser aucun voile résiduel sur fond clair — cf. le `floor`
 * du script d'extraction, `alnua-mark.png` avait le même souci de fond noir
 * opaque visible sur dégradé, corrigé ici par un vrai canal alpha).
 */
export function AlnuaStar({
  size = 52,
  glow = false,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars -- no-op, cf. doc ci-dessus
  animated = true,
  className,
  glowColorRgb = "192,138,114",
}: AlnuaStarProps) {
  return (
    <div
      className={cn("relative inline-block shrink-0", className)}
      style={{ width: size, height: size }}
      role="img"
      aria-label="ALNUA"
    >
      <Image
        src={SYMBOL_SRC}
        alt=""
        fill
        sizes={`${size}px`}
        className="object-contain"
        style={glow ? { filter: `drop-shadow(0 0 10px rgba(${glowColorRgb},.55))` } : undefined}
      />
    </div>
  );
}
