"use client";

import { useRef, useEffect, useState } from "react";
import { Send, Bot, User, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { sendCOOInstruction } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";
import { useCooStore } from "@/store/coo-store";
import { cn } from "@/lib/utils";

const DEFAULT_SUGGESTIONS = [
  "Priorise mes tickets Naïa",
  "Génère du contenu pour Wyrdheim",
  "Analyse les feedbacks Eve",
  "Qu'est-ce qui est urgent aujourd'hui ?",
];

const CEO_SUGGESTIONS = [
  "Lance le pipeline sur une issue Naïa",
  "Génère le brief de la semaine",
  "Quel est l'état de mes projets ?",
  "Connecte Gmail",
];

interface COOChatProps {
  variant?: "default" | "ceo";
  /** Hides the card header when rendered inside CooDrawer */
  embedded?: boolean;
}

export function COOChat({ variant = "default", embedded = false }: COOChatProps) {
  const consumePrefillMessage = useCooStore((s) => s.consumePrefillMessage);
  const suggestions =
    variant === "ceo" ? CEO_SUGGESTIONS : DEFAULT_SUGGESTIONS;
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Salut Emilie. Je suis ton COO — dis-moi ce que tu veux faire, je m'occupe du reste.",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    const prefill = consumePrefillMessage();
    if (prefill) setInput(prefill);
  }, [consumePrefillMessage]);

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
      const response = await sendCOOInstruction(content);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: response,
          timestamp: new Date(),
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content:
            "Impossible de joindre le COO. Vérifie que l'API tourne sur localhost:8000.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card
      className={cn(
        "flex h-full flex-col border-white/[0.08] bg-surface/80 backdrop-blur-sm",
        !embedded && "min-h-[480px]"
      )}
    >
      {!embedded ? (
        <CardHeader className="border-b border-white/[0.06] pb-3">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-copper/20 ring-1 ring-copper/30">
              <Bot className="h-4 w-4 text-copper" />
            </div>
            <div>
              <CardTitle className="text-base text-ivory">Parler au COO</CardTitle>
              <p className="text-xs text-titanium">Langage naturel · délégation auto</p>
            </div>
          </div>
        </CardHeader>
      ) : null}

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
                      ? "bg-white/10"
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
                      : "bg-white/[0.04] text-ivory/75 ring-1 ring-white/[0.06]"
                  )}
                >
                  <p className="whitespace-pre-line">{msg.content}</p>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex items-center gap-2 text-xs text-titanium">
                <Loader2 className="h-3.5 w-3.5 animate-spin text-copper" />
                Le COO réfléchit…
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        </ScrollArea>

        <div className="shrink-0 space-y-2 border-t border-white/[0.06] p-4">
          <div className="flex flex-wrap gap-1.5">
            {suggestions.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => handleSend(s)}
                disabled={loading}
                className="rounded-full bg-white/[0.04] px-2.5 py-1 text-[11px] text-titanium/80 ring-1 ring-white/[0.06] transition hover:bg-copper/10 hover:text-copper-glow disabled:opacity-50"
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
              placeholder="Ex: Triage les tickets Wyrdheim…"
              disabled={loading}
              className="border-white/[0.08] bg-white/[0.03] text-ivory placeholder:text-titanium/60 focus-visible:ring-copper/40"
            />
            <Button
              type="submit"
              disabled={loading || !input.trim()}
              aria-label="Envoyer au COO"
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
