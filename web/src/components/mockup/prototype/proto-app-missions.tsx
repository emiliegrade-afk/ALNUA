"use client";

import {
  CheckCircle2,
  ChevronDown,
  ClipboardList,
  Filter,
  MoreHorizontal,
  Plus,
  Rocket,
} from "lucide-react";
import { agents, missions, type ProtoMission } from "./proto-data";
import { ProtoAvatar, ProtoPanel, ProtoProgressRing, ProtoSectionHeader } from "./proto-shared";

const COLS: [ProtoMission["status"], string][] = [
  ["backlog", "Backlog"],
  ["progress", "In Progress"],
  ["review", "In Review"],
  ["done", "Completed"],
];

export function ProtoAppMissions() {
  return (
    <div className="page">
      <ProtoSectionHeader
        title="MISSIONS"
        desc="Pilotage des missions et du flux de travail du département APP"
        icon={<ClipboardList size={16} />}
      >
        <button type="button" className="outline-btn">
          <Filter size={14} /> Filtres
        </button>
        <button type="button" className="primary-btn">
          <Plus size={15} /> Nouvelle mission
        </button>
      </ProtoSectionHeader>

      <div className="pipeline-toolbar">
        <span>PROJECT PIPELINE</span>
        <div>
          <button type="button" className="small-select">
            Task parter: <b>Active</b>
            <ChevronDown size={13} />
          </button>
          <button type="button" className="icon-btn">
            <MoreHorizontal size={15} />
          </button>
        </div>
      </div>

      <div className="mission-layout">
        <div className="kanban">
          {COLS.map(([key, label]) => (
            <div className={`kanban-col ${key}`} key={key}>
              <div className="col-head">
                <b>{label}</b>
                <span>
                  <Plus size={14} />
                  <MoreHorizontal size={14} />
                </span>
              </div>
              {missions
                .filter((m) => m.status === key)
                .map((m) => (
                  <MissionCard key={m.title} mission={m} />
                ))}
            </div>
          ))}
        </div>
        <aside className="activity-panel">
          <ProtoPanel title="REAL-TIME ACTIVITY">
            <div className="activity-list">
              {[
                ["Théo Laurent a ajouté une tâche à Academy", "theo", "Academy", "22:14"],
                ["QA Team a approuvé API v2", "hao", "NAÏA", "22:11"],
                ["Inès Moreau a partagé une maquette", "ines", "NAÏA", "22:08"],
                ["Rayan Koné a déployé une mise à jour", "rayan", "Academy", "22:06"],
                ["Sam Rivera a démarré les tests", "sam", "NAÏA", "22:02"],
              ].map(([text, agent, proj, time]) => (
                <div className="activity-row" key={text}>
                  <ProtoAvatar agent={agent} />
                  <span>
                    {text}
                    <small>{proj}</small>
                  </span>
                  <time>{time}</time>
                </div>
              ))}
            </div>
            <button type="button" className="text-btn">
              Voir toute l'activité
            </button>
          </ProtoPanel>
        </aside>
      </div>

      <div className="mission-detail">
        <div className="team-panel">
          <ProtoPanel title="ÉQUIPE APP">
            <div className="team-list">
              {(["hao", "theo", "ines", "rayan", "sam"] as const).map((id, i) => {
                const a = agents.find((x) => x.id === id);
                return (
                  <div className="team-row" key={id}>
                    <ProtoAvatar agent={id} />
                    <span>
                      <b>{a?.name}</b>
                      <small>{a?.role}</small>
                    </span>
                    <strong>{[64, 76, 85, 52, 65][i]}%</strong>
                  </div>
                );
              })}
            </div>
            <button type="button" className="open-btn">
              Voir toute l'équipe
            </button>
          </ProtoPanel>
        </div>

        <div className="selected-mission">
          <div className="selected-head">
            <ProtoAvatar agent="theo" size="md" />
            <div>
              <span className="eyebrow">PROJET : ACADEMY — MODULE MESSAGES</span>
              <h2>Développement du système de messagerie temps réel</h2>
              <p>Spécialité · React Native · TypeScript · Expo · Mobile Architecture</p>
            </div>
            <ProtoProgressRing value={78} />
          </div>
          <div className="mission-tabs">
            <button type="button" className="active">
              Mission en cours
            </button>
            <button type="button">Discussion</button>
            <button type="button">Notes privées</button>
            <button type="button">Performance</button>
          </div>
          <div className="mission-content">
            <div className="task-list">
              {["Message List", "Message Input", "Realtime Connection", "Push Notifications", "Unread Badge"].map(
                (x, i) => (
                  <div className="task-row" key={x}>
                    <CheckCircle2 className={i < 2 ? "done-icon" : ""} size={16} />
                    <span>{x}</span>
                    <div className="bar">
                      <i style={{ width: `${[100, 100, 66, 60, 4][i]}%` }} />
                    </div>
                    <small>{["Terminé", "Terminé", "En cours", "À venir", "À venir"][i]}</small>
                  </div>
                ),
              )}
            </div>
            <div className="discussion">
              <div className="chat-message">
                <ProtoAvatar agent="theo" />
                <p>J'ai terminé le Message List. Je passe maintenant sur la connexion temps réel.</p>
              </div>
              <div className="chat-message mine">
                <p>Parfait. Priorité haute sur les notifications. Tiens-moi au courant.</p>
              </div>
              <div className="chat-input">
                Envoyer un message à Théo...
                <button type="button">
                  <Rocket size={14} />
                </button>
              </div>
            </div>
            <div className="mini-analytics">
              <div>
                <span>Tâches ouvertes</span>
                <b>32</b>
              </div>
              <div>
                <span>Tâches terminées</span>
                <b>115</b>
              </div>
              <div>
                <span>Qualité du code</span>
                <b>94%</b>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function MissionCard({ mission: m }: { mission: ProtoMission }) {
  return (
    <article className="mission-card">
      <h4>{m.title}</h4>
      <div className="mission-meta">
        <span className="priority">{m.priority}</span>
        {m.tags.map((t) => (
          <span key={t}>{t}</span>
        ))}
      </div>
      <div className="mission-people">
        {m.people.map((id) => (
          <ProtoAvatar key={id} agent={id} />
        ))}
      </div>
      <div className="mission-progress">
        <span>Progress</span>
        <div className="bar">
          <i style={{ width: `${m.progress}%` }} />
        </div>
        <span>{m.progress}%</span>
      </div>
    </article>
  );
}
