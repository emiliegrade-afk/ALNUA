"use client";

import { useRef, useEffect, useState } from "react";
import { Send, Bot, User, Loader2, ThumbsUp, ThumbsDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  sendAssistantMessage,
  submitAgentFeedback,
  type AssistantAgentMode,
  type ChatMessage,
} from "@/lib/assistant-api";
import { useCooStore } from "@/store/coo-store";
import { cn } from "@/lib/utils";

const AGENT_META: Record<
  AssistantAgentMode,
  { label: string; welcome: string; suggestions: string[] }
> = {
  auto: {
    label: "Auto",
    welcome:
      "Salut Emilie. **Nadia** filtre le quotidien (mails, agenda, brief, Academy). **Aria** garde la stratégie (R&D, plans, délégation).",
    suggestions: [
      "Priorités du jour",
      "Rapport de la nuit Academy",
      "Rédige un mail de relance partenaire",
      "Lance une investigation R&D sur…",
    ],
  },
  coo: {
    label: "Aria",
    welcome:
      "Aria ici — COO. Stratégie, R&D, tickets, délégation. Pour mails / brief / Academy → bascule sur Nadia.",
    suggestions: [
      "Lance une investigation R&D sur…",
      "Priorise mes tickets",
      "Note cette idée : …",
      "Délègue au pôle APP…",
    ],
  },
  secretary: {
    label: "Nadia",
    welcome:
      "Nadia Faure, secrétaire. Mails, contrats, agenda, brief du matin et rapport Academy — en langage naturel.",
    suggestions: [
      "Priorités du jour",
      "Rapport de la nuit",
      "Trier mes emails urgents",
      "Connecte mon Gmail",
    ],
  },
};

interface AssistantChatProps {
  defaultAgent?: AssistantAgentMode;
  variant?: "default" | "ceo" | "secretary";
  embedded?: boolean;
  className?: string;
}

export function AssistantChat({
  defaultAgent = "auto",
  variant = "default",
  embedded = false,
  className,
}: AssistantChatProps) {
  const [agentMode, setAgentMode] = useState<AssistantAgentMode>(defaultAgent);
  const meta = AGENT_META[agentMode];

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content: meta.welcome,
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [feedbackPending, setFeedbackPending] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const consumePrefillMessage = useCooStore((s) => s.consumePrefillMessage);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    const prefill = consumePrefillMessage();
    if (prefill) setInput(prefill);
  }, [consumePrefillMessage]);

  useEffect(() => {
    setMessages([
      {
        id: `welcome-${agentMode}`,
        role: "assistant",
        content: AGENT_META[agentMode].welcome,
        timestamp: new Date(),
      },
    ]);
  }, [agentMode]);

  async function handleSend(text?: string) {
    const content = (text ?? input).trim();
    if (!content || loading) return;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const result = await sendAssistantMessage(content, agentMode);
      const header =
        agentMode === "auto"
          ? `**${result.agent_name}**\n\n`
          : "";
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `${header}${result.response}`,
          timestamp: new Date(),
          agentId: result.agent_id,
          responseId: result.response_id,
          userMessage: content,
          issueCreated: result.issue_created,
          issueNumber: result.issue_number,
          issueUrl: result.issue_url,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content:
            "Impossible de joindre le Hub. Vérifie que l'API tourne (port 8003) et que Next.js proxy /api/hub répond.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function handleFeedback(
    msg: ChatMessage,
    rating: 1 | -1
  ) {
    if (!msg.responseId || !msg.agentId || feedbackPending) return;
    setFeedbackPending(msg.id);
    try {
      const result = await submitAgentFeedback({
        agent_id: msg.agentId,
        response_id: msg.responseId,
        rating,
        original_message: msg.userMessage,
        original_response: msg.content,
      });
      if (rating === -1 && result.regen_response) {
        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content: result.regen_response ?? "Regénération échouée.",
            timestamp: new Date(),
            agentId: msg.agentId,
          },
        ]);
      }
    } catch {
      /* silent — feedback is best-effort */
    } finally {
      setFeedbackPending(null);
    }
  }

  const title =
    variant === "secretary"
      ? "Parler à Nadia"
      : variant === "ceo"
        ? "Assistants CEO"
        : "Assistants ALNUA";

  return (
    <Card
      className={cn(
        "flex h-full flex-col border-copper/15 bg-surface/80 backdrop-blur-sm",
        !embedded && "min-h-[480px]",
        className
      )}
    >
      {/* Toggle always visible — even in drawer — so Auto / Aria / Nadia is clear */}
      <CardHeader className="border-b border-copper/10 pb-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-copper/20 ring-1 ring-copper/30">
                <Bot className="h-4 w-4 text-copper" />
              </div>
              <div>
                <CardTitle className="text-base text-ivory">{title}</CardTitle>
                <p className="text-xs text-titanium">
                  {embedded
                    ? "Auto route · ou force Aria / Nadia"
                    : "Langage naturel · Aria & Nadia"}
                </p>
              </div>
            </div>
            <div className="flex rounded-lg bg-obsidian-deep/50 p-0.5 ring-1 ring-copper/15">
              {(["auto", "coo", "secretary"] as const).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => setAgentMode(mode)}
                  className={cn(
                    "rounded-md px-2.5 py-1 text-[11px] font-medium transition",
                    agentMode === mode
                      ? "bg-copper/25 text-copper-glow"
                      : "text-titanium hover:text-ivory"
                  )}
                >
                  {AGENT_META[mode].label}
                </button>
              ))}
            </div>
          </div>
        </CardHeader>

      <CardContent className="flex min-h-0 flex-1 flex-col gap-3 overflow-hidden p-0">
        <ScrollArea className="min-h-0 flex-1">
          <div className="space-y-4 px-4 pb-4 pt-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={cn(
                  "flex gap-2.5 animate-fade-in",
                  msg.role === "user" ? "flex-row-reverse" : "flex-row"
                )}
              >
                <div
                  className={cn(
                    "flex h-7 w-7 shrink-0 items-center justify-center rounded-full",
                    msg.role === "user"
                      ? "bg-obsidian/60"
                      : "bg-copper/20 ring-1 ring-copper/30"
                  )}
                >
                  {msg.role === "user" ? (
                    <User className="h-3.5 w-3.5 text-ivory/75" />
                  ) : (
                    <Bot className="h-3.5 w-3.5 text-copper" />
                  )}
                </div>
                <div
                  className={cn(
                    "max-w-[85%] rounded-xl px-3.5 py-2.5 text-sm leading-relaxed",
                    msg.role === "user"
                      ? "bg-copper/20 text-ivory"
                      : "bg-obsidian-deep/50 text-ivory/75 ring-1 ring-copper/15"
                  )}
                >
                  <p className="whitespace-pre-line">{msg.content}</p>
                  {msg.issueCreated && msg.issueUrl ? (
                    <div className="mt-2 rounded-lg border border-copper/20 bg-copper/5 p-3">
                      <p className="text-xs font-medium text-copper">
                        Issue créée
                      </p>
                      <a
                        href={msg.issueUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-titanium transition-colors hover:text-copper"
                      >
                        #{msg.issueNumber} — GitHub →
                      </a>
                    </div>
                  ) : null}
                  {msg.role === "assistant" &&
                  msg.responseId &&
                  msg.agentId &&
                  msg.id !== "welcome" &&
                  !msg.id.startsWith("welcome-") ? (
                    <div className="mt-2 flex gap-1">
                      <button
                        type="button"
                        title="Utile"
                        disabled={feedbackPending === msg.id}
                        onClick={() => handleFeedback(msg, 1)}
                        className="rounded p-1 text-titanium transition hover:bg-emerald-500/10 hover:text-emerald-400 disabled:opacity-40"
                      >
                        <ThumbsUp className="h-3.5 w-3.5" />
                      </button>
                      <button
                        type="button"
                        title="Pas utile — regénère"
                        disabled={feedbackPending === msg.id}
                        onClick={() => handleFeedback(msg, -1)}
                        className="rounded p-1 text-titanium transition hover:bg-red-500/10 hover:text-red-400 disabled:opacity-40"
                      >
                        <ThumbsDown className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ) : null}
                </div>
              </div>
            ))}
            {loading ? (
              <div className="flex items-center gap-2 text-xs text-titanium">
                <Loader2 className="h-3.5 w-3.5 animate-spin text-copper" />
                Réponse en cours…
              </div>
            ) : null}
            <div ref={bottomRef} />
          </div>
        </ScrollArea>

        <div className="shrink-0 space-y-2 border-t border-copper/10 p-4">
          <div className="flex flex-wrap gap-1.5">
            {meta.suggestions.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => handleSend(s)}
                disabled={loading}
                className="rounded-full bg-obsidian-deep/50 px-2.5 py-1 text-[11px] text-titanium/80 ring-1 ring-copper/15 transition hover:bg-copper/10 hover:text-copper-glow disabled:opacity-50"
              >
                {s}
              </button>
            ))}
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex gap-2"
          >
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ex : Rapport de la nuit, ou rédige un mail à…"
              disabled={loading}
              className="border-copper/15 bg-obsidian-deep/50 text-ivory placeholder:text-titanium/60 focus-visible:ring-copper/40"
            />
            <Button
              type="submit"
              disabled={loading || !input.trim()}
              aria-label="Envoyer"
              className="shrink-0 bg-copper hover:bg-copper"
            >
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </CardContent>
    </Card>
  );
}
