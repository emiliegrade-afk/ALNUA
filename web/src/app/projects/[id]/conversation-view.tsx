"use client";

import { useEffect, useRef, useState } from "react";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { devAppInstruction } from "@/lib/pole-api";
import type { BureauAgentDef } from "@/lib/agent-bureau";
import { C } from "../../app-v2/shared";

/* Panel 5 (Conversation agent) — même principe honnête que ChatPanel
   (app-v2/team.tsx) : seul dev_app a un canal d'instruction réel câblé,
   les autres agents reçoivent un message système explicite plutôt qu'une
   fausse réponse. Réécrit ici en version pleine page (liste de
   conversations + thread) plutôt que le petit panneau de l'onglet Équipe. */

const INSTRUCTION_HANDLERS: Record<string, (text: string) => Promise<{ result: string }>> = {
  dev_app: devAppInstruction,
};

interface ChatMsg {
  author: string;
  text: string;
  time: string;
  me: boolean;
  pending?: boolean;
}

function now() {
  return new Date().toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

export function ConversationView({
  agents,
  initialAgentId,
  onBack,
}: {
  agents: BureauAgentDef[];
  initialAgentId: string;
  onBack: () => void;
}) {
  const [activeId, setActiveId] = useState(initialAgentId);
  const [messagesByAgent, setMessagesByAgent] = useState<Record<string, ChatMsg[]>>({});
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const active = agents.find((a) => a.id === activeId) ?? agents[0];
  const messages = messagesByAgent[active?.id ?? ""] ?? [];

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages.length]);

  async function send() {
    const text = draft.trim();
    if (!text || sending || !active) return;
    const time = now();
    setMessagesByAgent((m) => ({ ...m, [active.id]: [...(m[active.id] ?? []), { author: "Toi", text, time, me: true }] }));
    setDraft("");

    const handler = INSTRUCTION_HANDLERS[active.id];
    if (!handler) {
      setMessagesByAgent((m) => ({
        ...m,
        [active.id]: [
          ...(m[active.id] ?? []),
          {
            author: "Système",
            text: `${active.name.split(" ")[0]} n'a pas encore de canal d'instruction directe câblé.`,
            time: now(),
            me: false,
          },
        ],
      }));
      return;
    }

    setSending(true);
    setMessagesByAgent((m) => ({
      ...m,
      [active.id]: [...(m[active.id] ?? []), { author: active.name.split(" ")[0], text: "…", time, me: false, pending: true }],
    }));
    try {
      const res = await handler(text);
      setMessagesByAgent((m) => ({
        ...m,
        [active.id]: (m[active.id] ?? [])
          .filter((msg) => !msg.pending)
          .concat({ author: active.name.split(" ")[0], text: res.result, time: now(), me: false }),
      }));
    } catch {
      setMessagesByAgent((m) => ({
        ...m,
        [active.id]: (m[active.id] ?? [])
          .filter((msg) => !msg.pending)
          .concat({ author: "Système", text: "L'agent n'a pas répondu (Hub injoignable).", time: now(), me: false }),
      }));
    } finally {
      setSending(false);
    }
  }

  if (!active) return null;

  return (
    <div className="flex flex-col gap-3">
      <button type="button" onClick={onBack} className="flex w-fit items-center gap-1.5 text-[11px]" style={{ color: C.warm }}>
        ← Retour à la fiche agent
      </button>

      <div className="flex h-[520px] overflow-hidden rounded-xl border" style={{ borderColor: C.line }}>
        <div className="flex w-[220px] shrink-0 flex-col border-r" style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}>
          <p className="px-3 py-2.5 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
            CONVERSATIONS
          </p>
          <div className="alnua-scroll flex-1 overflow-y-auto">
            {agents.map((a) => (
              <button
                key={a.id}
                type="button"
                onClick={() => setActiveId(a.id)}
                className="flex w-full items-center gap-2 px-3 py-2 text-left"
                style={{ background: a.id === active.id ? "rgba(200,127,78,.12)" : "transparent" }}
              >
                <AgentAvatar agentId={a.id} name={a.name} size={30} />
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-[11px] font-medium" style={{ color: C.ivory }}>
                    {a.name}
                  </span>
                  <span className="block text-[9px]" style={{ color: C.faint }}>
                    {INSTRUCTION_HANDLERS[a.id] ? "En ligne" : "Pas de canal direct"}
                  </span>
                </span>
              </button>
            ))}
          </div>
        </div>

        <div className="flex min-w-0 flex-1 flex-col">
          <div className="flex items-center gap-2.5 border-b px-4 py-3" style={{ borderColor: C.line }}>
            <AgentAvatar agentId={active.id} name={active.name} size={34} />
            <div>
              <p className="text-[12.5px] font-semibold" style={{ color: C.ivory }}>
                {active.name}
              </p>
              <p className="text-[9.5px]" style={{ color: C.faint }}>
                {active.role}
              </p>
            </div>
          </div>

          <div ref={scrollRef} className="alnua-scroll flex-1 overflow-y-auto px-4 py-3">
            {messages.length === 0 ? (
              <p className="py-6 text-center text-[10.5px]" style={{ color: C.faint }}>
                Aucun message pour l&apos;instant — écris à {active.name.split(" ")[0]} pour démarrer la conversation.
              </p>
            ) : (
              <div className="flex flex-col gap-2.5">
                {messages.map((m, i) => (
                  <div key={i} className={`flex ${m.me ? "justify-end" : "justify-start"}`}>
                    <div
                      className="max-w-[70%] rounded-xl px-3 py-2 text-[11.5px]"
                      style={{
                        background: m.me ? "rgba(200,127,78,.18)" : "rgba(255,255,255,.04)",
                        color: m.author === "Système" ? C.faint : C.ivory,
                      }}
                    >
                      <p>{m.text}</p>
                      <p className="mt-1 flex items-center gap-1 text-[8.5px]" style={{ color: C.faint }}>
                        {m.time}
                        {m.me ? <span>✓✓</span> : null}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex items-center gap-2 border-t p-3" style={{ borderColor: C.line }}>
            <input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder="Écrire un message…"
              className="min-w-0 flex-1 rounded-lg border bg-transparent px-3 py-2 text-[11.5px] outline-none"
              style={{ borderColor: C.line, color: C.ivory }}
            />
            <button
              type="button"
              onClick={() => void send()}
              disabled={sending || !draft.trim()}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full disabled:opacity-40"
              style={{ background: C.copper, color: "#0E1014" }}
            >
              ➤
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
