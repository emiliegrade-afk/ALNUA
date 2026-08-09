"use client";

import { Bot, User, Plus } from "lucide-react";
import { useStreamingText } from "@/hooks/use-streaming-text";
import type { BrainstormMessage } from "@/lib/brainstorm";
import { cn } from "@/lib/utils";

interface ChatMessageProps {
  message: BrainstormMessage;
  streaming?: boolean;
  onAddRoadmap?: (content: string) => void;
}

export function ChatMessageBubble({
  message,
  streaming = false,
  onAddRoadmap,
}: ChatMessageProps) {
  const isUser = message.role === "user";
  const { displayed, isStreaming } = useStreamingText(
    message.content,
    streaming && !isUser
  );

  const text = streaming && !isUser ? displayed : message.content;

  return (
    <div
      className={cn(
        "group flex gap-3 animate-fade-in",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          isUser
            ? "bg-obsidian-deep/60"
            : "bg-copper/15 ring-1 ring-copper/25"
        )}
      >
        {isUser ? (
          <User className="h-4 w-4 text-ivory/75" />
        ) : (
          <Bot className="h-4 w-4 text-copper" />
        )}
      </div>

      <div className={cn("max-w-[80%] space-y-1", isUser && "items-end")}>
        <div
          className={cn(
            "relative rounded-2xl px-4 py-3 text-sm leading-relaxed",
            isUser
              ? "bg-copper/25 text-ivory"
              : "bg-obsidian-deep/50 text-ivory/75 ring-1 ring-copper/15"
          )}
        >
          <p className="whitespace-pre-line">{text}</p>
          {isStreaming && (
            <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-copper" />
          )}

          {!isUser && onAddRoadmap && !isStreaming && (
            <button
              type="button"
              onClick={() => onAddRoadmap(message.content)}
              className="mt-2 flex items-center gap-1 rounded-md px-2 py-1 text-[11px] text-copper/80 transition hover:bg-copper/10 hover:text-copper-glow"
            >
              <Plus className="h-3 w-3" />
              Roadmap
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
