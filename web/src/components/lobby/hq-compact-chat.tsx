"use client";

import { useEffect, useRef, useState } from "react";
import { Loader2, Send } from "lucide-react";
import {
  sendAssistantMessage,
  type AssistantAgentMode,
} from "@/lib/assistant-api";
import { cn } from "@/lib/utils";

const QUICK_PROMPTS: Record<AssistantAgentMode, string[]> = {
  auto: ["Priorités du jour", "État pipeline"],
  coo: ["Priorités du jour", "État pipeline Academy"],
  secretary: ["Rapport de la nuit", "Trier emails urgents"],
};

interface HqCompactChatProps {
  mode: AssistantAgentMode;
  agentFirstName: string;
  className?: string;
}

export function HqCompactChat({
  mode,
  agentFirstName,
  className,
}: HqCompactChatProps) {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<
    Array<{ role: "user" | "assistant"; text: string }>
  >([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(text?: string) {
    const content = (text ?? input).trim();
    if (!content || loading) return;

    setMessages((prev) => [...prev, { role: "user", text: content }]);
    setInput("");
    setLoading(true);

    try {
      const result = await sendAssistantMessage(content, mode);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: result.response },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "Hub indisponible — vérifie que l'API tourne.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={cn("flex min-h-0 flex-col", className)}>
      <div className="min-h-0 flex-1 space-y-2 overflow-y-auto px-1 py-1">
        {messages.length === 0 ? (
          <p className="px-1 font-body text-[10px] leading-relaxed text-titanium/55">
            Parle à {agentFirstName} en langage naturel.
          </p>
        ) : (
          messages.map((msg, i) => (
            <div
              key={`${msg.role}-${i}`}
              className={cn(
                "rounded-lg px-2 py-1.5 font-body text-[10px] leading-relaxed",
                msg.role === "user"
                  ? "ml-4 bg-copper/15 text-ivory"
                  : "mr-2 border border-copper/10 bg-obsidian/60 text-titanium/85",
              )}
            >
              {msg.text}
            </div>
          ))
        )}
        {loading ? (
          <div className="flex items-center gap-1.5 px-1 text-[9px] text-titanium/50">
            <Loader2 className="h-3 w-3 animate-spin text-copper" />
            Réponse…
          </div>
        ) : null}
        <div ref={bottomRef} />
      </div>

      <div className="shrink-0 space-y-1.5 border-t border-copper/10 pt-2">
        <div className="flex flex-wrap gap-1">
          {QUICK_PROMPTS[mode].map((prompt) => (
            <button
              key={prompt}
              type="button"
              disabled={loading}
              onClick={() => handleSend(prompt)}
              className="rounded-full border border-copper/15 bg-copper/5 px-2 py-0.5 font-body text-[8px] text-titanium/70 transition hover:border-copper/30 hover:text-copper disabled:opacity-40"
            >
              {prompt}
            </button>
          ))}
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void handleSend();
          }}
          className="flex gap-1"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Message à ${agentFirstName}…`}
            disabled={loading}
            className="min-w-0 flex-1 rounded-lg border border-copper/15 bg-obsidian/80 px-2 py-1.5 font-body text-[10px] text-ivory placeholder:text-titanium/40 focus:border-copper/40 focus:outline-none"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            aria-label="Envoyer"
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-copper text-obsidian transition hover:bg-copper/90 disabled:opacity-40"
          >
            <Send className="h-3.5 w-3.5" />
          </button>
        </form>
      </div>
    </div>
  );
}

/** Map office id → assistant routing mode (when chat is available). */
export function assistantModeForOffice(
  officeId: string,
): AssistantAgentMode | null {
  switch (officeId) {
    case "secretary":
      return "secretary";
    case "direction":
    case "ceo":
      return "coo";
    default:
      return null;
  }
}
