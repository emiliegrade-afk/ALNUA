"use client";

import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { CONSOLE_POLES } from "@/lib/console/departments";
import { AlnuaLogo } from "@/components/console/alnua-logo";

export function MockupDirectory() {
  return (
    <div className="mx-auto max-w-6xl space-y-6 pb-20">
      <header className="flex items-center gap-3">
        <AlnuaLogo variant="icon" size={36} staticMark />
        <div>
          <p className="text-[10px] uppercase tracking-[0.2em] text-titane/55">ALNUA / PÔLES</p>
          <h1 className="font-title text-2xl font-semibold text-ivoire">Départements</h1>
        </div>
      </header>

      <p className="max-w-2xl text-sm leading-relaxed text-titane/65">
        Onze pôles composent l&apos;entreprise virtuelle ALNUA. Chaque bureau est dirigé par des agents
        IA spécialisés, accessibles depuis cette annuaire.
      </p>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {CONSOLE_POLES.map((pole) => {
          const Icon = pole.icon;
          return (
            <Link
              key={pole.id}
              href={pole.href}
              className="group relative flex flex-col rounded-xl border border-bronze-faint bg-obsidian/60 p-5 transition-all duration-300 hover:border-copper/40 hover:bg-obsidian-2"
            >
              <div className="flex items-start justify-between">
                <span className="font-mono text-xs tabular-nums text-copper/70">{pole.code}</span>
                <Icon className="h-5 w-5 text-copper/70 transition-colors group-hover:text-copper" />
              </div>
              <h2 className="mt-3 font-title text-base font-semibold text-ivoire">
                {pole.name.replace("Bureau ", "").replace("Pôle ", "")}
              </h2>
              <p className="mt-1 text-xs text-titane/60">{pole.tagline}</p>
              <p className="mt-3 text-[11px] leading-relaxed text-titane/50">{pole.description}</p>
              <span className="mt-4 inline-flex items-center gap-1 text-[11px] uppercase tracking-widest text-copper/70 transition-colors group-hover:text-copper">
                Ouvrir
                <ChevronRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5" />
              </span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
