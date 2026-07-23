import Link from "next/link";
import { Bot, Zap, Shield, Layers, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AlnuaLogo } from "@/components/brand/alnua-logo";

const FEATURES = [
  {
    icon: Bot,
    title: "20 agents IA",
    desc: "COO, PM, QA, Dev, R&D — chacun avec persona, mémoire et operating spec.",
  },
  {
    icon: Zap,
    title: "Auto-amélioration",
    desc: "Boucles d'apprentissage, fix pipeline autonome, cycle R&D hebdo.",
  },
  {
    icon: Shield,
    title: "Production-ready",
    desc: "Multi-tenant, cache LLM, rate limiting, API /v1, observabilité Prometheus.",
  },
  {
    icon: Layers,
    title: "Orchestration",
    desc: "Workflows, parallélisme async, plugins marketplace, feedback 👍/👎.",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-ivory">
      <header className="border-b border-white/[0.06] px-6 py-4">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <Link href="/landing" className="flex items-center gap-2">
            <AlnuaLogo variant="icon" height={32} staticMark />
            <span className="font-display text-lg font-semibold tracking-tight text-copper-glow">
              ALNUA Hub
            </span>
          </Link>
          <nav className="flex gap-4 text-sm text-titanium">
            <Link href="/docs" className="hover:text-ivory">
              Docs
            </Link>
            <Link href="/ceo" className="hover:text-ivory">
              Ouvrir le Hub
            </Link>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-20">
        <section className="text-center">
          <p className="mb-4 text-sm uppercase tracking-widest text-copper">
            Plateforme agents IA
          </p>
          <h1 className="font-display text-4xl font-bold leading-tight md:text-5xl">
            Ton équipe IA
            <br />
            <span className="text-copper-glow">qui apprend et livre</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-titanium">
            ALNUA Hub orchestre 20 agents spécialisés — specs, code, marketing,
            comptabilité, R&D — avec mémoire persistante et pipelines autonomes.
          </p>
          <div className="mt-10 flex flex-wrap justify-center gap-4">
            <Button asChild className="bg-copper hover:bg-copper/90">
              <Link href="/ceo">
                Démarrer <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" className="border-white/10">
              <Link href="/openroom">Explorer les rooms</Link>
            </Button>
          </div>
        </section>

        <section className="mt-24 grid gap-6 sm:grid-cols-2">
          {FEATURES.map(({ icon: Icon, title, desc }) => (
            <div
              key={title}
              className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-6"
            >
              <Icon className="mb-3 h-8 w-8 text-copper" />
              <h3 className="font-display text-lg font-semibold">{title}</h3>
              <p className="mt-2 text-sm text-titanium">{desc}</p>
            </div>
          ))}
        </section>

        <section className="mt-24 rounded-xl border border-copper/20 bg-copper/5 p-8 text-center">
          <h2 className="font-display text-2xl font-semibold">
            Prête pour la production
          </h2>
          <p className="mt-3 text-titanium">
            Tests CI, backup S3, Grafana, OpenTelemetry, Redis + RQ worker.
          </p>
          <p className="mt-6 text-xs text-titanium/60">
            ALNUA · Multi-tenant · API versionnée · Feedback loop
          </p>
        </section>
      </main>
    </div>
  );
}
