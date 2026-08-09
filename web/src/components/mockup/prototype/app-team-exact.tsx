"use client";

import { useState } from "react";
import { MessageCircle, UserPlus } from "lucide-react";
import {
  APP_TEAM_ACTIVITY,
  APP_TEAM_IDS,
  APP_TEAM_LOADS,
  APP_TEAM_MISSIONS,
  APP_TEAM_RADAR,
  APP_TEAM_SKILLS,
  APP_TEAM_STATS,
  type AppTeamId,
} from "./app-team-data";
import { agents } from "./proto-data";
import { ProtoAvatar, ProtoProgressRing, ProtoSectionHeader } from "./proto-shared";

/** Onglet Équipe APP — fiche agent ChatGPT (panel 2, 28 juil.). */
export function AppTeamExact() {
  const [selected, setSelected] = useState<AppTeamId>("theo");
  const agent = agents.find((a) => a.id === selected)!;
  const load = APP_TEAM_LOADS[selected];
  const skills = APP_TEAM_SKILLS[selected];
  const mission = APP_TEAM_MISSIONS[selected];
  const activity = APP_TEAM_ACTIVITY[selected];
  const stats = APP_TEAM_STATS[selected];

  return (
    <div className="pb-6">
      <ProtoSectionHeader
        title="ÉQUIPE"
        desc="Agents du département APP · fiches & charge"
        icon={<span className="text-[11px] font-semibold">E</span>}
      >
        <button type="button" className="outline-btn">
          Filtres
        </button>
        <button type="button" className="primary-btn">
          <UserPlus size={14} /> Ajouter un agent
        </button>
      </ProtoSectionHeader>

      <div className="grid gap-3 xl:grid-cols-[220px_minmax(0,1fr)]">
        <aside className="panel overflow-hidden">
          <div className="panel-title">
            <span>AGENTS APP</span>
          </div>
          <div className="p-1.5">
            {APP_TEAM_IDS.map((id) => {
              const a = agents.find((x) => x.id === id)!;
              const active = selected === id;
              return (
                <button
                  key={id}
                  type="button"
                  onClick={() => setSelected(id)}
                  className={`mb-1 flex w-full items-center gap-2 rounded-lg border px-2 py-2 text-left transition ${
                    active
                      ? "border-[rgba(224,164,119,0.45)] bg-[rgba(224,164,119,0.08)]"
                      : "border-transparent hover:bg-[#0d141b]"
                  }`}
                >
                  <ProtoAvatar agent={id} size="sm" />
                  <span className="min-w-0 flex-1">
                    <b className="block truncate text-[11px] text-[#e8e2da]">{a.name}</b>
                    <small className="block truncate text-[8px] text-[#6e767f]">{a.role}</small>
                  </span>
                  <span className="text-[9px] text-[#e0a477]">{APP_TEAM_LOADS[id].charge}%</span>
                </button>
              );
            })}
          </div>
        </aside>

        <section className="panel overflow-hidden">
          <div className="flex flex-wrap items-start justify-between gap-3 border-b border-[rgba(255,255,255,0.07)] p-4">
            <div className="flex items-start gap-3">
              <ProtoAvatar agent={selected} size="md" />
              <div>
                <h2 className="text-[18px] font-medium text-[#e8e2da]">{agent.name}</h2>
                <p className="text-[11px] text-[#8e959c]">
                  {selected === "theo" ? "Senior Mobile Engineer" : agent.role}
                </p>
                <span className="mt-1 inline-flex items-center gap-1.5 text-[10px] text-[#5ed69a]">
                  <span className="dot green" /> En activité
                </span>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-4">
              <LoadStat label="Disponibilité" value={load.disponibility} />
              <LoadStat label="Charge actuelle" value={load.charge} />
              <div className="hidden text-[9px] text-[#6e767f] lg:block">
                <div>2 ans 4 mois</div>
                <div>Europe/Paris · FR — EN</div>
              </div>
              <div className="flex gap-2">
                <button type="button" className="outline-btn">
                  <MessageCircle size={14} /> Discuter
                </button>
                <button type="button" className="primary-btn">
                  Assigner une tâche
                </button>
              </div>
            </div>
          </div>

          <div className="department-tabs border-b border-[rgba(255,255,255,0.07)] px-2" style={{ padding: 0, margin: 0 }}>
            <div className="tabs">
              {["Aperçu", "Missions", "Activité", "Compétences", "Documents", "Mémoire", "Paramètres"].map(
                (t, i) => (
                  <button key={t} type="button" className={i === 0 ? "active" : undefined}>
                    {t}
                  </button>
                ),
              )}
            </div>
          </div>

          <div className="grid gap-3 p-3 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
            <div className="space-y-3">
              <div className="rounded-xl border border-[rgba(255,255,255,0.07)] bg-[#0b1118] p-3">
                <p className="mb-2 text-[9px] tracking-[1.5px] text-[#9b9fa5]">MISSION EN COURS</p>
                <div className="flex items-center justify-between gap-2">
                  <div>
                    <h3 className="text-[13px] text-[#e8e2da]">{mission.current}</h3>
                    <p className="text-[9px] text-[#6e767f]">Deadline · Sprint 19 · Haute priorité</p>
                  </div>
                  <ProtoProgressRing value={mission.progress} small />
                </div>
                <div className="bar mt-2">
                  <i style={{ width: `${mission.progress}%` }} />
                </div>
              </div>

              <div className="rounded-xl border border-[rgba(255,255,255,0.07)] bg-[#0b1118] p-3">
                <p className="mb-1 text-[9px] tracking-[1.5px] text-[#9b9fa5]">PROCHAINE MISSION</p>
                <h3 className="text-[12px] text-[#e8e2da]">{mission.next}</h3>
                <p className="mt-1 text-[9px] text-[#6e767f]">Estimation 3h 20 · Priorité moyenne</p>
              </div>

              <div className="rounded-xl border border-[rgba(255,255,255,0.07)] bg-[#0b1118] p-3">
                <p className="mb-2 text-[9px] tracking-[1.5px] text-[#9b9fa5]">ACTIVITÉ RÉCENTE</p>
                <div className="space-y-2">
                  {activity.map((row) => (
                    <div key={row.text} className="flex items-start gap-2 border-b border-[rgba(255,255,255,0.05)] pb-2">
                      <ProtoAvatar agent={selected} size="sm" />
                      <div className="min-w-0 flex-1">
                        <p className="text-[10px] text-[#9aa1a8]">
                          <b className="text-[#e8e2da]">{agent.name.split(" ")[0]}</b> {row.text}
                        </p>
                        <p className="text-[8px] text-[#5f6871]">{row.time}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <div className="rounded-xl border border-[rgba(255,255,255,0.07)] bg-[#0b1118] p-3">
                <p className="mb-2 text-[9px] tracking-[1.5px] text-[#9b9fa5]">COMPÉTENCES</p>
                <div className="space-y-2">
                  {skills.map((s) => (
                    <div key={s.name}>
                      <div className="mb-0.5 flex justify-between text-[9px]">
                        <span className="text-[#9aa1a8]">{s.name}</span>
                        <span className="text-[#e0a477]">{s.pct}%</span>
                      </div>
                      <div className="bar">
                        <i style={{ width: `${s.pct}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-xl border border-[rgba(255,255,255,0.07)] bg-[#0b1118] p-3">
                <p className="mb-2 text-[9px] tracking-[1.5px] text-[#9b9fa5]">RADAR</p>
                <RadarSvg values={APP_TEAM_RADAR.map((r) => r.value)} />
                <div className="mt-2 flex flex-wrap justify-center gap-2">
                  {APP_TEAM_RADAR.map((r) => (
                    <span key={r.label} className="text-[8px] text-[#6e767f]">
                      {r.label} <b className="text-[#e0a477]">{r.value}</b>
                    </span>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                {stats.map(([v, l]) => (
                  <div key={l} className="rounded-xl border border-[rgba(255,255,255,0.07)] bg-[#0b1118] px-3 py-2.5">
                    <p className="text-[16px] font-medium text-[#e8e2da]">{v}</p>
                    <p className="text-[8px] text-[#6e767f]">{l}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

function LoadStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="min-w-[110px]">
      <div className="mb-1 flex justify-between text-[8px] text-[#6e767f]">
        <span>{label}</span>
        <span className="text-[#e0a477]">{value}%</span>
      </div>
      <div className="bar">
        <i style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

function RadarSvg({ values }: { values: number[] }) {
  const cx = 70;
  const cy = 70;
  const r = 52;
  const n = values.length;
  const pts = values
    .map((v, i) => {
      const ang = -Math.PI / 2 + (i * 2 * Math.PI) / n;
      const rr = (v / 100) * r;
      return `${cx + rr * Math.cos(ang)},${cy + rr * Math.sin(ang)}`;
    })
    .join(" ");
  const grid = [0.4, 0.7, 1].map((f) => {
    const ring = Array.from({ length: n }, (_, i) => {
      const ang = -Math.PI / 2 + (i * 2 * Math.PI) / n;
      return `${cx + r * f * Math.cos(ang)},${cy + r * f * Math.sin(ang)}`;
    }).join(" ");
    return <polygon key={f} points={ring} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="1" />;
  });

  return (
    <svg viewBox="0 0 140 140" className="mx-auto h-[140px] w-[140px]">
      {grid}
      <polygon points={pts} fill="rgba(224,164,119,0.22)" stroke="#e0a477" strokeWidth="1.5" />
    </svg>
  );
}
