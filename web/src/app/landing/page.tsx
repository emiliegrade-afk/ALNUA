import Link from "next/link";
import {
  ArrowRight,
  ChevronUp,
  Sparkles,
  Star,
  Circle,
  Target,
  type LucideIcon,
} from "lucide-react";
import { AlnuaStar } from "@/components/brand/alnua-star";
import { Button } from "@/components/ui/button";

const VALUES: { icon: LucideIcon; label: string; desc: string }[] = [
  { icon: ChevronUp, label: "Convergence", desc: "Réunir les talents dans la même forge." },
  { icon: Sparkles, label: "Innovation", desc: "Faire émerger l'idée avant les autres." },
  { icon: Star, label: "Excellence", desc: "Tolérance zéro pour l'à-peu-près." },
  { icon: Circle, label: "Transformation", desc: "Convertir la matière en lumière." },
  { icon: Target, label: "Impact", desc: "Mesurer ce qui compte vraiment." },
];

const SUB_BRANDS = [
  {
    name: "ALNUA LABS",
    desc: "Recherche & prototypes — l'atelier où naissent les futurs produits.",
    href: "/rnd-v2",
  },
  {
    name: "ALNUA STUDIOS",
    desc: "Jeux & mondes narratifs — Wyrdheim et les univers à venir.",
    href: "/gaming",
  },
  {
    name: "ALNUA ROBOTICS",
    desc: "Hardware embarqué — Eve et la perception située.",
    href: "/robo",
  },
  {
    name: "ALNUA WORLDS",
    desc: "Applications & expériences — Naïa, Nomad et les suivantes.",
    href: "/app",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-obsidian text-ivory">
      {/* ─── Header ─── */}
      <header className="border-b border-copper/10 px-6 py-5">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <Link href="/landing" className="flex items-center gap-3" aria-label="ALNUA">
            <AlnuaStar size={28} animated={false} />
            <span className="font-title text-sm font-medium tracking-[0.35em] text-gradient-bronze">
              ALNUA
            </span>
          </Link>
          <nav className="flex items-center gap-6 font-body text-xs tracking-widest uppercase text-titanium">
            <Link href="/docs" className="transition hover:text-ivory">
              Docs
            </Link>
            <Link href="/ceo" className="transition hover:text-ivory">
              Ouvrir le Hub
            </Link>
          </nav>
        </div>
      </header>

      {/* ─── Hero — THE FORGE ─── */}
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 bg-radial-glow opacity-70" />
        <div className="pointer-events-none absolute inset-0 forge-grid opacity-40" />
        <div className="relative mx-auto max-w-4xl px-6 py-28 text-center">
          <div className="mb-10 flex justify-center">
            <AlnuaStar size={120} glow animated />
          </div>
          <p className="forge-heading text-[11px] text-copper/80">
            The Forge
          </p>
          <h1 className="mt-4 font-title text-6xl font-medium tracking-[0.35em] text-ivory md:text-7xl">
            ALNUA
          </h1>
          <p className="mt-8 font-title text-sm tracking-[0.3em] text-titanium md:text-base">
            IMAGINATION <span className="text-copper/60">•</span> TECHNOLOGY{" "}
            <span className="text-copper/60">•</span> CREATION
          </p>
          <p className="mt-2 font-title text-sm tracking-[0.3em] text-gradient-bronze md:text-base">
            TRANSFORMED INTO REALITY
          </p>
          <div className="mt-12 flex flex-wrap justify-center gap-4">
            <Button asChild className="bg-copper text-obsidian hover:bg-copper-light">
              <Link href="/ceo">
                Ouvrir le Hub
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button
              asChild
              variant="outline"
              className="border-copper/30 text-copper hover:bg-copper/10 hover:text-copper-light"
            >
              <Link href="#forge">Découvrir la forge</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* ─── Manifeste ─── */}
      <section id="forge" className="border-y border-copper/10 bg-obsidian-deep/40">
        <div className="mx-auto max-w-3xl px-6 py-20 text-center">
          <p className="font-title text-2xl leading-relaxed text-ivory md:text-3xl">
            Technology should serve humanity.
            <br />
            <span className="text-titanium/70">Not the opposite.</span>
          </p>
          <p className="mt-6 font-body text-sm tracking-wide text-titanium">
            The future is not discovered. It is built.
          </p>
        </div>
      </section>

      {/* ─── 5 Valeurs ─── */}
      <section className="mx-auto max-w-6xl px-6 py-20">
        <p className="forge-heading text-center text-[11px] text-copper/80">
          Valeurs
        </p>
        <h2 className="mt-3 text-center font-title text-2xl tracking-[0.2em] text-ivory">
          Cinq principes, une forge
        </h2>
        <div className="mt-12 grid grid-cols-2 gap-px overflow-hidden rounded-xl border border-copper/10 bg-copper/10 md:grid-cols-5">
          {VALUES.map(({ icon: Icon, label, desc }) => (
            <div
              key={label}
              className="group bg-obsidian p-6 transition-colors hover:bg-obsidian-2"
            >
              <Icon className="h-6 w-6 text-copper transition-transform duration-300 group-hover:scale-110" />
              <p className="mt-4 font-title text-xs tracking-[0.2em] text-ivory">
                {label.toUpperCase()}
              </p>
              <p className="mt-2 font-body text-xs leading-relaxed text-titanium/70">
                {desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ─── 4 Sous-marques ─── */}
      <section className="border-t border-copper/10 bg-obsidian-deep/30">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <p className="forge-heading text-center text-[11px] text-copper/80">
            Divisions
          </p>
          <h2 className="mt-3 text-center font-title text-2xl tracking-[0.2em] text-ivory">
            Une marque, quatre territoires
          </h2>
          <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {SUB_BRANDS.map((sb) => (
              <Link
                key={sb.name}
                href={sb.href}
                className="group relative flex flex-col rounded-xl border border-copper/15 bg-obsidian/60 p-6 transition-all duration-300 hover:border-copper/40 hover:bg-obsidian-2"
              >
                <div className="mb-4 h-px w-8 bg-copper/40 transition-all duration-300 group-hover:w-12 group-hover:bg-copper" />
                <p className="font-title text-sm tracking-[0.25em] text-ivory">
                  {sb.name}
                </p>
                <p className="mt-3 font-body text-xs leading-relaxed text-titanium/70">
                  {sb.desc}
                </p>
                <span className="mt-6 inline-flex items-center gap-1 font-body text-[11px] uppercase tracking-widest text-copper/70 transition-colors group-hover:text-copper">
                  Entrer
                  <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5" />
                </span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA final ─── */}
      <section className="border-t border-copper/10">
        <div className="mx-auto max-w-3xl px-6 py-24 text-center">
          <AlnuaStar size={64} animated={false} className="mx-auto" />
          <h2 className="mt-8 font-title text-3xl tracking-[0.15em] text-ivory">
            Building the future of
            <br />
            <span className="text-gradient-bronze">human-centered technology.</span>
          </h2>
          <div className="mt-10 flex justify-center">
            <Button asChild className="bg-copper text-obsidian hover:bg-copper-light">
              <Link href="/ceo">
                Entrer dans la forge
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </section>

      {/* ─── Footer ─── */}
      <footer className="border-t border-copper/10 bg-obsidian-deep/60">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 py-8 sm:flex-row">
          <div className="flex items-center gap-3">
            <AlnuaStar size={20} animated={false} />
            <span className="font-title text-[11px] tracking-[0.3em] text-titanium">
              ALNUA <span className="text-copper/60">·</span> THE FORGE
            </span>
          </div>
          <p className="font-body text-[11px] tracking-widest uppercase text-titanium/50">
            Imagination <span className="text-copper/40">•</span> Technology{" "}
            <span className="text-copper/40">•</span> Creation
          </p>
        </div>
      </footer>
    </div>
  );
}
