"use client";

/** Hero maquette — scène seule (PLAY / LEARN / RELAX / CONNECT déjà dans l’asset). */
export function LoungeHero() {
  return (
    <section className="relative h-[240px] overflow-hidden rounded-2xl border border-white/5 sm:h-[280px] lg:h-[300px]">
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{ backgroundImage: "url(/lounge/hero-scene.png)" }}
        aria-hidden
      />
      <div
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(180deg, rgba(8,9,12,0.25) 0%, transparent 35%, rgba(8,9,12,0.55) 100%)",
        }}
        aria-hidden
      />
    </section>
  );
}
