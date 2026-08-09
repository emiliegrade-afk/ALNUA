"use client";

import { useState } from "react";
import {
  ChevronRight,
  Filter,
  FolderKanban,
  Grid2X2,
  List,
  Plus,
} from "lucide-react";
import { projects, type ProtoProject } from "./proto-data";
import { ProtoAvatar, ProtoPanel, ProtoProgressRing, ProtoSectionHeader } from "./proto-shared";

export function ProtoAppProjects() {
  const [filter, setFilter] = useState("Tous");
  const filtered =
    filter === "Tous"
      ? projects
      : projects.filter((p) =>
          filter === "Actifs"
            ? p.status === "En développement"
            : filter === "En validation"
              ? p.status === "En validation"
              : filter === "Terminés"
                ? p.status === "Stable"
                : true,
        );

  return (
    <div>
      <ProtoSectionHeader
        title="PROJETS"
        desc="Vue d'ensemble de tous les projets du département APP"
        icon={<FolderKanban size={16} />}
      >
        <button type="button" className="outline-btn">
          <Filter size={14} /> Filtres
        </button>
        <button type="button" className="icon-btn">
          <Grid2X2 size={15} />
        </button>
        <button type="button" className="icon-btn">
          <List size={15} />
        </button>
        <button type="button" className="primary-btn">
          <Plus size={15} /> Nouveau projet
        </button>
      </ProtoSectionHeader>

      <div className="filter-tabs">
        {(["Tous", "Actifs", "En validation", "Terminés", "Archivés"] as const).map((f) => (
          <button
            key={f}
            type="button"
            className={filter === f ? "active" : ""}
            onClick={() => setFilter(f)}
          >
            {f}
            <span>
              {f === "Tous" ? 8 : f === "Actifs" ? 3 : f === "En validation" ? 2 : f === "Terminés" ? 2 : 1}
            </span>
          </button>
        ))}
      </div>

      <div className="projects-layout">
        <div className="project-grid">
          {filtered.map((p) => (
            <ProjectCard key={p.name} project={p} />
          ))}
          <div className="new-project-card">
            <Plus size={30} />
            <b>Nouveau projet</b>
            <span>Créer un nouveau projet dans le département APP</span>
          </div>
        </div>
        <ProjectAside />
      </div>
    </div>
  );
}

function ProjectCard({ project: p }: { project: ProtoProject }) {
  return (
    <article className="project-card">
      <div className={`project-cover cover-${p.image}`}>
        <div className="cover-glow" />
        <span>{p.name}</span>
      </div>
      <div className="project-body">
        <div className="project-heading">
          <div>
            <h3>{p.name}</h3>
            <p>{p.type}</p>
          </div>
          <ProtoProgressRing value={p.progress} small />
        </div>
        <div className="project-status">
          <span
            className={`status ${p.status === "Stable" ? "green" : p.status === "En validation" ? "amber" : "blue"}`}
          >
            {p.status}
          </span>
          <span>{p.sprint}</span>
        </div>
        <div className="phase-line">
          {["IDÉE", "DESIGN", "DEV", "QA", "RELEASE"].map((x, i) => (
            <span key={x} className="contents">
              <i className={i <= p.phase ? "on" : ""} />
              {i < 4 ? <b className={i < p.phase ? "on" : ""} /> : null}
            </span>
          ))}
        </div>
        <div className="phase-labels">
          {["IDÉE", "DESIGN", "DEV", "QA", "RELEASE"].map((x) => (
            <span key={x}>{x}</span>
          ))}
        </div>
        <div className="project-stats">
          <span>
            <b>{p.agents}</b>Agents
          </span>
          <span>
            <b>{p.tasks}</b>Tâches
          </span>
          <span>
            <b>{p.updates}</b>MAJ
          </span>
        </div>
        <div className="last-activity">
          <ProtoAvatar agent={p.name === "NAÏA" ? "theo" : "hao"} />
          <span>
            Dernière activité
            <br />
            <b>{p.name === "NAÏA" ? "Théo Laurent" : "Hao Chen"}</b> · mise à jour
          </span>
          <small>il y a {p.name === "NAÏA" ? "12 min" : "35 min"}</small>
        </div>
        <button type="button" className="open-btn">
          Ouvrir le projet <ChevronRight size={14} />
        </button>
      </div>
    </article>
  );
}

function ProjectAside() {
  return (
    <aside className="project-aside">
      <ProtoPanel title="RÉSUMÉ DES PROJETS">
        <div className="donut-summary">
          <div className="donut">
            <b>8</b>
            <span>Projets</span>
          </div>
          <div className="legend">
            <p>
              <i className="green-bg" />3 <span>Actifs</span>
            </p>
            <p>
              <i className="amber-bg" />2 <span>En validation</span>
            </p>
            <p>
              <i className="blue-bg" />2 <span>Terminés</span>
            </p>
            <p>
              <i className="gray-bg" />1 <span>Archivés</span>
            </p>
          </div>
        </div>
      </ProtoPanel>
      <ProtoPanel title="ACTIVITÉ RÉCENTE GLOBALE">
        <div className="activity-list">
          {[
            ["Théo Laurent a terminé NotificationService.ts", "theo", "NAÏA", "22:14"],
            ["Hao Chen a mis à jour NUAWAY", "hao", "NUAWAY", "22:03"],
            ["Inès Moreau attend votre validation", "ines", "Academy", "21:55"],
            ["Rayan Koné a déployé la version 2.4.1", "rayan", "ALNUA Hub", "21:42"],
            ["Sam Rivera a commenté le plan utilisateur", "sam", "Nwiro", "21:30"],
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
          Voir toute l'activité <ChevronRight size={13} />
        </button>
      </ProtoPanel>
      <ProtoPanel title="MÉTRIQUES GLOBALES">
        <div className="metric-grid">
          {[
            ["Agents impliqués", "28", "+12%"],
            ["Tâches totales", "325", "+8%"],
            ["MAJ cette semaine", "67", "+15%"],
            ["Projets en avance", "2", "+100%"],
          ].map(([label, value, delta]) => (
            <div className="metric" key={label}>
              <span>{label}</span>
              <b>{value}</b>
              <em>{delta}</em>
              <div className="spark" />
            </div>
          ))}
        </div>
      </ProtoPanel>
    </aside>
  );
}
