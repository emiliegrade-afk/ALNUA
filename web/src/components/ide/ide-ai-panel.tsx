"use client";

import { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import { Bot, Loader2, Send, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface CoachMessage {
  role: "user" | "assistant";
  content: string;
}

export function IdeAiPanel({
  messages,
  input,
  loading,
  hermesOk,
  onInputChange,
  onSend,
  onClose,
}: {
  messages: CoachMessage[];
  input: string;
  loading: boolean;
  hermesOk: boolean;
  onInputChange: (v: string) => void;
  onSend: () => void;
  onClose: () => void;
}) {
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  return (
    <aside className="flex h-full min-h-0 flex-col bg-obsidian-2/95">
      <div className="flex shrink-0 items-center justify-between border-b border-bronze-faint px-3 py-2">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-bronze-bright" />
          <div>
            <p className="font-title text-xs text-ivoire">Luca</p>
            <p className="text-[10px] text-titane/50">Coach · contexte fichier</p>
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="text-[10px] text-titane/50 hover:text-ivoire"
        >
          Fermer
        </button>
      </div>

      {hermesOk ? (
        <p className="shrink-0 border-b border-bronze-faint px-3 py-1 text-[10px] text-bronze/70">
          Hermes skills chargés
        </p>
      ) : null}

      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-3 alnua-scroll">
        {messages.map((m, i) => (
          <div
            key={i}
            className={cn(
              "rounded-lg px-3 py-2 text-xs leading-relaxed",
              m.role === "user"
                ? "ml-6 bg-bronze/12 text-ivoire"
                : "mr-4 border border-bronze-faint/50 bg-obsidian text-titane/85",
            )}
          >
            {m.role === "assistant" ? (
              <div className="prose prose-invert prose-xs max-w-none prose-p:my-1 prose-pre:my-2 prose-pre:bg-obsidian-deep prose-pre:text-[11px] prose-code:text-bronze-bright">
                <ReactMarkdown>{m.content}</ReactMarkdown>
              </div>
            ) : (
              <p className="whitespace-pre-wrap">{m.content}</p>
            )}
          </div>
        ))}
        {loading ? (
          <div className="flex items-center gap-2 text-xs text-titane/50">
            <Loader2 className="h-3.5 w-3.5 animate-spin text-bronze" />
            Luca réfléchit…
          </div>
        ) : null}
        <div ref={endRef} />
      </div>

      <div className="shrink-0 border-t border-bronze-faint p-2">
        <div className="flex gap-2 rounded-lg border border-bronze-faint bg-obsidian p-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => onInputChange(e.target.value)}
            rows={2}
            placeholder="Explique ce code, propose un fix, ou pose une question…"
            className="min-h-[2.5rem] min-w-0 flex-1 resize-none bg-transparent text-xs text-ivoire outline-none placeholder:text-titane/35"
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                onSend();
              }
            }}
          />
          <Button
            type="button"
            size="sm"
            className="h-8 shrink-0 self-end"
            disabled={!input.trim() || loading}
            onClick={onSend}
          >
            <Send className="h-3.5 w-3.5" />
          </Button>
        </div>
        <p className="mt-1.5 flex items-center gap-1 px-1 text-[10px] text-titane/40">
          <Bot className="h-3 w-3" />
          Entrée envoyer · Maj+Entrée nouvelle ligne
        </p>
      </div>
    </aside>
  );
}
