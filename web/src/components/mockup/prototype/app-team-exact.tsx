"use client";

import { ProtoAvatar, ProtoProgressRing, ProtoSectionHeader } from "./proto-shared";

const TEAM = [
  { id: "hao", name: "Hao Chen", role: "Dev · Backend & API", load: 82, skills: ["Node", "Postgres", "API"], tasks: 24 },
  { id: "theo", name: "Théo Laurent", role: "Dev · Applications mobiles", load: 78, skills: ["React Native", "Expo", "TS"], tasks: 31 },
  { id: "ines", name: "Inès Moreau", role: "UI/UX Designer", load: 65, skills: ["Figma", "Design system", "Proto"], tasks: 18 },
  { id: "rayan", name: "Rayan Koné", role: "DevOps · Intégration", load: 71, skills: ["CI/CD", "Docker", "GitHub"], tasks: 15 },
  { id: "sam", name: "Sam Rivera", role: "PM · Gestion de projet", load: 58, skills: ["Roadmap", "Specs", "Priorisation"], tasks: 22 },
];

const ACTIVITY = [
  { who: "theo", text: "a terminé MessageList · Academy", time: "22:14" },
  { who: "hao", text: "a déployé API v2 · NAÏA", time: "22:03" },
  { who: "ines", text: "attend validation maquette · Hub", time: "21:55" },
  { who: "rayan", text: "a mergé pipeline CI · Hub", time: "21:42" },
  { who: "sam", text: "a priorisé Sprint 19 · NAÏA", time: "21:30" },
];

/** Onglet Équipe APP — roster + charge + activité. */
export function AppTeamExact() {
  return (
    <div className="grid gap-3 pb-6 xl:grid-cols-[minmax(0,1fr)_260px]">
      <div className="min-w-0 space-y-3">
        <ProtoSectionHeader
          title="ÉQUIPE"
          desc="Agents du département APP · charge et spécialités"
          icon={<span className="text-[11px] font-semibold">E</span>}
        >
          <button type="button" className="outline-btn">
            Filtres
          </button>
          <button type="button" className="primary-btn">
            + Ajouter un agent
          </button>
        </ProtoSectionHeader>

        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
          {TEAM.map((a) => (
            <article
              key={a.id}
              className="rounded-xl border border-[rgba(255,255,255,0.07)] bg-[#0b1118] p-3"
            >
              <div className="flex items-start gap-3">
                <ProtoAvatar agent={a.id} size="md" />
                <div className="min-w-0 flex-1">
                  <h3 className="text-[13px] font-medium text-[#e8e2da]">{a.name}</h3>
                  <p className="text-[9px] text-[#6e767f]">{a.role}</p>
                </div>
                <ProtoProgressRing value={a.load} small />
              </div>
              <div className="mt-3 flex flex-wrap gap-1">
                {a.skills.map((s) => (
                  <span
                    key={s}
                    className="rounded bg-[#151c24] px-1.5 py-0.5 text-[7px] text-[#7e8790]"
                  >
                    {s}
                  </span>
                ))}
              </div>
              <div className="mt-3 flex items-center justify-between border-t border-[rgba(255,255,255,0.07)] pt-2 text-[9px]">
                <span className="text-[#6e767f]">{a.tasks} tâches actives</span>
                <span className="text-[#e0a477]">{a.load}% charge</span>
              </div>
              <div className="bar mt-2">
                <i style={{ width: `${a.load}%` }} />
              </div>
            </article>
          ))}
        </div>
      </div>

      <aside className="space-y-3">
        <section className="rounded-xl border border-[rgba(255,255,255,0.07)] bg-[#0b1118] p-3">
          <p className="mb-2 text-[9px] tracking-[1.5px] text-[#9b9fa5]">RÉSUMÉ ÉQUIPE</p>
          <div className="grid grid-cols-2 gap-2">
            {[
              ["Agents", "5"],
              ["Charge moy.", "71%"],
              ["Tâches", "110"],
              ["En avance", "2"],
            ].map(([l, v]) => (
              <div key={l} className="rounded-md bg-[#0d141b] px-2 py-2">
                <p className="text-[14px] font-medium text-[#e8e2da]">{v}</p>
                <p className="text-[8px] text-[#6e767f]">{l}</p>
              </div>
            ))}
          </div>
        </section>
        <section className="rounded-xl border border-[rgba(255,255,255,0.07)] bg-[#0b1118]">
          <div className="border-b border-[rgba(255,255,255,0.07)] px-3 py-2.5 text-[9px] tracking-[1.5px] text-[#9b9fa5]">
            ACTIVITÉ RÉCENTE
          </div>
          <div className="p-2">
            {ACTIVITY.map((a) => (
              <div key={a.text} className="flex gap-2 border-b border-[rgba(255,255,255,0.05)] py-2">
                <ProtoAvatar agent={a.who} size="sm" />
                <div className="min-w-0 flex-1">
                  <p className="text-[9px] leading-snug text-[#9aa1a8]">{a.text}</p>
                  <p className="mt-1 text-[8px] text-[#5f6871]">{a.time}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      </aside>
    </div>
  );
}
