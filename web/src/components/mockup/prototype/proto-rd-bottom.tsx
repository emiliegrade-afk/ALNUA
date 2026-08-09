"use client";

import { Rocket } from "lucide-react";
import { ProtoAvatar, ProtoPanel, ProtoProgressRing } from "./proto-shared";

/** Bas de page R&D — exploration / arbre / incubateur / décision (maquette ChatGPT). */
export function ProtoRdBottom() {
  return (
    <div className="rd-bottom">
      <ProtoPanel title="EXPLORATION AUTOMATISÉE">
        <div className="discovery">
          {[
            ["IA embarquée sur mobile", "Les modèles IA optimisés pour smartphones progressent.", "Opportunité", "nova"],
            ["Brevets Dyson", "Nouveaux brevets détectés sur les moteurs compacts.", "Technologie", "layla"],
            ["Croissance du marché", "Le marché des copilotes augmente de +28%.", "Tendance", "sam"],
          ].map(([title, desc, tag, agent]) => (
            <div key={title}>
              <ProtoAvatar agent={agent} />
              <span>
                <b>{title}</b>
                <small>{desc}</small>
              </span>
              <em>{tag}</em>
            </div>
          ))}
        </div>
        <button type="button" className="text-btn">
          Voir toutes les découvertes
        </button>
      </ProtoPanel>
      <ProtoPanel title="ARBRE DES IDÉES">
        <div className="idea-tree">
          <div className="tree-core">
            Nuaway
            <br />
            Copilot
          </div>
          <div className="tree-branch one">
            Plateforme
            <small>Mobile · Web · Desktop</small>
          </div>
          <div className="tree-branch two">
            Technologie
            <small>LLM léger · RAG · Edge IA</small>
          </div>
          <div className="tree-branch three">
            Marché cible
            <small>Créateurs · Nomades</small>
          </div>
        </div>
      </ProtoPanel>
      <ProtoPanel title="INCUBATEUR">
        <div className="flex flex-wrap gap-1 border-b border-[rgba(255,255,255,0.07)] px-2 py-2 text-[8px] text-[#7e8790]">
          {[
            ["Idée", "128"],
            ["Prototype", "24"],
            ["Validation", "12"],
            ["MVP", "6"],
            ["Projet", "3"],
          ].map(([l, v], i, arr) => (
            <span key={l} className="inline-flex items-center gap-1">
              <b className="text-[#e0a477]">{v}</b> {l}
              {i < arr.length - 1 ? <span className="text-[#3a424a]">→</span> : null}
            </span>
          ))}
        </div>
        <div className="incubator">
          {[
            ["NUA Copilot Mobile", 65, "Nova"],
            ["Robot Companion", 40, "Mira"],
            ["Health AI Companion", 90, "Axel"],
          ].map(([name, pct, owner]) => (
            <div key={name as string}>
              <span>{name}</span>
              <b>{pct}%</b>
              <div className="bar">
                <i style={{ width: `${pct}%` }} />
              </div>
              <small>{owner} · Responsable</small>
            </div>
          ))}
        </div>
        <button type="button" className="text-btn">
          Voir tout l&apos;incubateur
        </button>
      </ProtoPanel>
      <ProtoPanel title="DÉCISION COLLECTIVE">
        <div className="consensus">
          <p className="text-[8px] text-[#6e767f]">Copilot Nomade IA · 15 juin 2026</p>
          <ProtoProgressRing value={86} />
          <b>Consensus IA 86%</b>
          <span>LANCER LE MVP · Orienté créateurs nomades</span>
          <div className="mt-2 w-full space-y-1.5 text-left">
            {[
              ["aria", "GO", "98%"],
              ["nova", "GO", "94%"],
              ["mira", "MAYBE", "71%"],
              ["sam", "GO", "88%"],
            ].map(([id, vote, conf]) => (
              <div key={id} className="flex items-center gap-2">
                <ProtoAvatar agent={id} size="sm" />
                <span className="flex-1 text-[9px] text-[#9aa1a8]">{vote}</span>
                <span className="text-[9px] text-[#e0a477]">{conf}</span>
              </div>
            ))}
          </div>
          <button type="button" className="primary-btn mt-2 w-full justify-center">
            Créer le projet <Rocket size={14} />
          </button>
        </div>
      </ProtoPanel>
    </div>
  );
}
