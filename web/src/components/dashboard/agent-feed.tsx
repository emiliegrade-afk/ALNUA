"use client";

import { formatDistanceToNow } from "date-fns";
import { fr } from "date-fns/locale";
import {
  Bot,
  CheckCircle2,
  AlertCircle,
  Clock,
  Activity,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { AgentLog } from "@/lib/types";
import { cn } from "@/lib/utils";

interface AgentFeedProps {
  logs: AgentLog[];
  loading?: boolean;
}

const AGENT_COLORS: Record<string, string> = {
  coo_agent: "text-copper bg-copper/15",
  pm_agent: "text-copper bg-copper/15",
  qa_agent: "text-copper-dim bg-copper/10",
  content_agent: "text-copper-light bg-copper/15",
  brainstorm_agent: "text-copper bg-copper/15",
  spec_agent: "text-copper-light bg-copper/10",
};

function StatusIcon({ status }: { status: AgentLog["status"] }) {
  switch (status) {
    case "success":
      return <CheckCircle2 className="h-3.5 w-3.5 text-copper-light" />;
    case "error":
      return <AlertCircle className="h-3.5 w-3.5 text-red-400" />;
    case "pending":
      return <Clock className="h-3.5 w-3.5 text-copper-dim" />;
  }
}

export function AgentFeed({ logs, loading }: AgentFeedProps) {
  return (
    <Card className="border-copper/20 bg-obsidian-2/80 backdrop-blur-sm">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-titanium/80" />
          <div>
            <CardTitle className="text-base text-ivory">Activité agents</CardTitle>
            <p className="text-xs text-titanium">Feed temps réel · Supabase</p>
          </div>
        </div>
        <Badge variant="outline" className="border-white/10 text-titanium/80">
          {logs.length} events
        </Badge>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea className="h-[380px]">
          {loading ? (
            <div className="flex items-center justify-center py-12 text-sm text-titanium">
              Chargement du feed…
            </div>
          ) : logs.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-2 py-12 text-center">
              <Bot className="h-8 w-8 text-neutral-700" />
              <p className="text-sm text-titanium">Aucune action agent récente</p>
            </div>
          ) : (
            <ul className="divide-y divide-white/[0.04]">
              {logs.map((log, i) => (
                <li
                  key={log.id}
                  className="animate-fade-in px-4 py-3 transition hover:bg-white/[0.02]"
                  style={{ animationDelay: `${i * 40}ms` }}
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={cn(
                        "mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg",
                        AGENT_COLORS[log.agent_name] ?? "bg-white/5 text-titanium/80"
                      )}
                    >
                      <Bot className="h-3.5 w-3.5" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-ivory/90">
                          {log.agent_name.replace("_", " ")}
                        </span>
                        <StatusIcon status={log.status} />
                        <span className="text-[10px] text-titanium/60">
                          {formatDistanceToNow(new Date(log.created_at), {
                            addSuffix: true,
                            locale: fr,
                          })}
                        </span>
                      </div>
                      <p className="mt-0.5 text-xs font-medium text-copper-glow/80">
                        {log.action}
                      </p>
                      {log.input_summary && (
                        <p className="mt-1 line-clamp-1 text-[11px] text-titanium">
                          → {log.input_summary}
                        </p>
                      )}
                      {log.output_summary && (
                        <p className="mt-0.5 line-clamp-2 text-[11px] text-titanium/80">
                          {log.output_summary}
                        </p>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
