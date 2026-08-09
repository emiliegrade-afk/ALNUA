"use client";

import { useState } from "react";
import {
  BookOpen,
  BrainCircuit,
  CheckCircle2,
  FolderKanban,
  GitBranch,
  Grid2X2,
  Lightbulb,
  List,
  Plus,
  Rocket,
  Search,
  Settings2,
  Users,
  X,
} from "lucide-react";
import { agents, brainstorm, ideas, type ProtoIdea } from "./proto-data";
import { ProtoRdBottom } from "./proto-rd-bottom";
import { ProtoAvatar, ProtoProgressRing, ProtoSectionHeader } from "./proto-shared";

/** Page R&D Brainstorm — copie maquette Vite / ChatGPT (onglets visuels inclus). */
export function ProtoRdBrainstorm() {
  const [idea, setIdea] = useState("");
  const [messages, setMessages] = useState(brainstorm);
  const [selected, setSelected] = useState<ProtoIdea | null>(null);

  const send = () => {
    if (!idea.trim()) return;
    setMessages([...messages, ["Emilie", idea]]);
    setIdea("");
  };

  return (
    <div>
      <ProtoSectionHeader
        title="BRAINSTORM"
        desc="Espace de réflexion collective · agents IA + CEO"
        icon={<BrainCircuit size={16} />}
      >
        <button type="button" className="outline-btn">
          <Users size={14} /> 6 participants
        </button>
        <button type="button" className="primary-btn">
          <Plus size={15} /> Nouvelle session
        </button>
      </ProtoSectionHeader>

      <div className="rd-tabs">
        <button type="button" className="active">
          <Lightbulb size={15} /> Brainstorm
        </button>
        <button type="button">
          <BookOpen size={15} /> Centre R&D
        </button>
        <button type="button">
          <GitBranch size={15} /> Arbres
        </button>
        <button type="button">
          <FolderKanban size={15} /> Dossiers
        </button>
        <button type="button">
          <Search size={15} /> Explorer
        </button>
        <button type="button">
          <Rocket size={15} /> Incubateur
        </button>
        <button type="button">
          <Settings2 size={15} /> Paramètres
        </button>
      </div>

      <div className="rd-layout">
        <section className="brainstorm-panel panel">
          <div className="panel-head">
            <div>
              <span className="eyebrow">SESSION DE BRAINSTORM · COPILOT NOMADE IA</span>
              <h2>Création assistée hors ligne</h2>
            </div>
            <span className="live-pill">
              <span className="dot green" />
              En cours&nbsp;&nbsp;00:24:31
            </span>
          </div>
          <div className="participants">
            {(["aria", "nova", "mira", "layla", "sam"] as const).map((id) => (
              <div key={id}>
                <ProtoAvatar agent={id} />
                <span>{agents.find((a) => a.id === id)?.name.split(" ")[0]}</span>
              </div>
            ))}
            <div>
              <ProtoAvatar />
              <span>Emilie</span>
            </div>
          </div>
          <div className="grid gap-0 border-t border-[rgba(255,255,255,0.07)] lg:grid-cols-[minmax(0,1fr)_200px]">
            <div>
              <div className="chat-stream">
                {messages.map((m, i) => (
                  <div className="brain-msg" key={`${m[0]}-${i}`}>
                    <ProtoAvatar agent={(["aria", "nova", "mira", "sam", "ines"] as const)[i % 5]} />
                    <div>
                      <b>{m[0]}</b>
                      <time>14:{30 + i}</time>
                      <p>{m[1]}</p>
                    </div>
                    <span className="msg-actions">♡ · ↗</span>
                  </div>
                ))}
              </div>
              <div className="chat-compose">
                <input
                  value={idea}
                  onChange={(e) => setIdea(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && send()}
                  placeholder="Exprime ton idée, pose une question..."
                />
                <button type="button" onClick={send}>
                  <Rocket size={16} />
                </button>
              </div>
            </div>
            <aside className="border-l border-[rgba(255,255,255,0.07)] p-3">
              <p className="text-[9px] tracking-[1.5px] text-[#9b9fa5]">CONSENSUS IA</p>
              <div className="my-3 flex justify-center">
                <ProtoProgressRing value={72} />
              </div>
              <p className="text-center text-[10px] text-[#e8e2da]">72% Consensus global</p>
              <div className="mt-3 space-y-2">
                {[
                  ["Faisabilité", 83],
                  ["Innovation", 91],
                  ["ROI estimé", 78],
                  ["Risque", 22],
                  ["Urgence marché", 67],
                ].map(([label, pct]) => (
                  <div key={label as string}>
                    <div className="mb-0.5 flex justify-between text-[8px] text-[#7e8790]">
                      <span>{label}</span>
                      <span>{pct}%</span>
                    </div>
                    <div className="bar">
                      <i style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                ))}
              </div>
              <p className="mt-3 text-center text-[8px] text-[#5f6871]">6 / 6 agents ont exprimé leur position</p>
            </aside>
          </div>
        </section>

        <section className="pipeline panel">
          <div className="panel-head">
            <div>
              <span className="eyebrow">PIPELINE D'INNOVATION</span>
              <h2>128 idées</h2>
            </div>
            <div className="view-controls">
              <button type="button">
                <Grid2X2 size={14} />
              </button>
              <button type="button">
                <List size={14} />
              </button>
            </div>
          </div>
          <div className="idea-summary">
            <div>
              <b>128</b>
              <span>Total</span>
            </div>
            <div className="go">
              <b>29</b>
              <span>GO</span>
            </div>
            <div className="maybe">
              <b>45</b>
              <span>Maybe</span>
            </div>
            <div className="no">
              <b>36</b>
              <span>No</span>
            </div>
            <div>
              <b>18</b>
              <span>En attente</span>
            </div>
          </div>
          <div className="idea-grid">
            {ideas.map((x, i) => (
              <button type="button" className="idea-card" key={x.title} onClick={() => setSelected(x)}>
                <div className="idea-top">
                  <span className="idea-icon">
                    <Lightbulb size={15} />
                  </span>
                  <ProtoProgressRing value={x.score} small />
                </div>
                <h3>{x.title}</h3>
                <p>{x.desc}</p>
                <div className="idea-tags">
                  <span>IA</span>
                  <span>{i % 2 ? "Hardware" : "Mobile"}</span>
                  <span
                    style={{
                      color:
                        x.verdict === "GO"
                          ? "var(--green)"
                          : x.verdict === "MAYBE"
                            ? "var(--amber)"
                            : "var(--red)",
                    }}
                  >
                    {x.verdict}
                  </span>
                </div>
                <div className="idea-scores">
                  <span>
                    Marché <b>{x.market}/10</b>
                  </span>
                  <span>
                    Tech <b>{x.tech}/10</b>
                  </span>
                  <span>
                    Business <b>{x.business}/10</b>
                  </span>
                </div>
                <div className="idea-footer">
                  <ProtoAvatar agent={(["nova", "mira", "sam"] as const)[i % 3]} />
                  <span>+{i + 2}</span>
                  <small>Mis à jour il y a {i + 1}h</small>
                </div>
              </button>
            ))}
          </div>
        </section>
      </div>

      <ProtoRdBottom />

      {selected ? (
        <div className="modal-backdrop" onClick={() => setSelected(null)} role="presentation">
          <div className="idea-modal" onClick={(e) => e.stopPropagation()} role="dialog">
            <button type="button" className="close" onClick={() => setSelected(null)}>
              <X size={16} />
            </button>
            <span className="eyebrow">PROPOSITION · DOSSIER R&D</span>
            <h2>{selected.title}</h2>
            <p>{selected.desc}</p>
            <div className="decision-gauge">
              <ProtoProgressRing value={selected.score} />
              <div>
                <b>Faisabilité globale</b>
                <span>
                  Marché {selected.market}/10 · Tech {selected.tech}/10 · Business {selected.business}/10
                </span>
              </div>
            </div>
            <div className="modal-actions">
              <button type="button" className="outline-btn">
                Continuer le débat
              </button>
              <button type="button" className="primary-btn">
                Valider la proposition <CheckCircle2 size={15} />
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
