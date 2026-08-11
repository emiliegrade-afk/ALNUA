"use client";

import { Scale } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getAgentById } from "@/lib/agent-bureau";

const PERSONA = {
  name: "Solène Hariri",
  initials: "SH",
  role: "Avocate d'entreprise — UE / USA / Asie",
  catchphrase: "Avant de signer, on lit — partout où ça engage ALNUA.",
  personality:
    "Rigoureuse, internationale, prudente. Préfère un caveat de trop à une clause oubliée.",
  workStyle: "Analyse → risques → comparatif juridictions → next steps + disclaimer",
  fear: "Signature sans relecture",
  relations: ["Nadia (docs & escalade)", "Aria (partenariats stratégiques)", "Emilie (décision finale)"],
};

export function LegalPersonaCard() {
  const agent = getAgentById("legal_counsel");
  const skills = agent?.skills ?? [
    "Avis UE/USA/Asie",
    "Review contrats",
    "Pré-signature",
    "NDA & partenariats",
  ];

  return (
    <Card className="border-copper/30 bg-obsidian-2/90">
      <CardHeader>
        <CardTitle className="flex items-center gap-3 font-title text-base text-ivory">
          <span className="flex h-12 w-12 items-center justify-center rounded-full bg-copper/15 text-sm font-bold text-copper">
            {PERSONA.initials}
          </span>
          <span>
            <span className="block">{PERSONA.name}</span>
            <span className="mt-0.5 block text-[11px] font-normal tracking-wide text-titanium/70">
              {PERSONA.role}
            </span>
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 text-sm text-titanium/85">
        <p className="italic text-ivory/90">« {PERSONA.catchphrase} »</p>
        <p>{PERSONA.personality}</p>
        <div>
          <p className="label-caps mb-2 flex items-center gap-1.5 text-copper">
            <Scale className="h-3.5 w-3.5" />
            Skills
          </p>
          <ul className="flex flex-wrap gap-2">
            {skills.map((s) => (
              <li
                key={s}
                className="rounded border border-copper/25 bg-obsidian-1 px-2.5 py-1 text-xs text-ivory"
              >
                {s}
              </li>
            ))}
          </ul>
        </div>
        <div className="grid gap-2 text-xs sm:grid-cols-2">
          <p>
            <span className="text-titanium/50">Méthode — </span>
            {PERSONA.workStyle}
          </p>
          <p>
            <span className="text-titanium/50">Garde-fou — </span>
            {PERSONA.fear}
          </p>
        </div>
        <p className="text-xs">
          <span className="text-titanium/50">Contact — </span>
          {PERSONA.relations.join(" · ")}
        </p>
        <p className="text-[11px] text-titanium/50">
          Aide à la décision Hub — pas un avocat inscrit au barreau. Validation humaine
          avant toute signature.
        </p>
      </CardContent>
    </Card>
  );
}
