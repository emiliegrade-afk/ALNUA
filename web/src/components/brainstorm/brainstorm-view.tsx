"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { FileText, Loader2, Send } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  BrainstormEmpty,
  DEFAULT_SUGGESTIONS,
} from "@/components/brainstorm/brainstorm-empty";
import { ChatMessageBubble } from "@/components/brainstorm/chat-message";
import {
  ProjectSelector,
  scopeLabel,
  BRAINSTORM_GLOBAL_VALUE,
  NEW_PROJECT_VALUE,
  type ProjectScope,
} from "@/components/brainstorm/project-selector";
import { RoadmapModal } from "@/components/brainstorm/roadmap-modal";
import { SessionSidebar } from "@/components/brainstorm/session-sidebar";
import { SummaryResultModal } from "@/components/brainstorm/summary-result-modal";
import {
  fetchBrainstormSession,
  fetchBrainstormSessions,
  fetchProjects,
  fetchSessionSummary,
  sendBrainstormMessage,
  summarizeBrainstormSession,
  WELCOME_MESSAGE,
  type BrainstormMessage,
  type BrainstormSession,
  type Project,
  type SummarizeResult,
} from "@/lib/brainstorm";
function ChatInput({
  input,
  loading,
  onInputChange,
  onSend,
}: {
  input: string;
  loading: boolean;
  onInputChange: (value: string) => void;
  onSend: () => void;
}) {
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSend();
      }}
      className="mx-auto flex w-full max-w-2xl gap-2"
    >
      <Textarea
        value={input}
        onChange={(e) => onInputChange(e.target.value)}
        placeholder="Une idée, une question, une direction…"
        disabled={loading}
        rows={2}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            onSend();
          }
        }}
        className="min-h-[52px] resize-none border-copper/15 bg-white/[0.02] text-ivory/90 placeholder:text-titanium/60 focus-visible:ring-copper/30"
      />
      <Button
        type="submit"
        disabled={loading || !input.trim()}
        aria-label="Envoyer le message"
        className="h-auto shrink-0 bg-copper px-4 hover:bg-copper"
      >
        <Send className="h-4 w-4" />
      </Button>
    </form>
  );
}

export function BrainstormView() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [scope, setScope] = useState<ProjectScope>(BRAINSTORM_GLOBAL_VALUE);
  const [projectId, setProjectId] = useState<string | null>(null);

  const [sessions, setSessions] = useState<BrainstormSession[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(true);

  useEffect(() => {
    setSidebarCollapsed(window.innerWidth < 1024);
  }, []);

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<BrainstormMessage[]>([]);
  const [hasStarted, setHasStarted] = useState(false);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [streamingId, setStreamingId] = useState<string | null>(null);

  const [roadmapOpen, setRoadmapOpen] = useState(false);
  const [roadmapDefaults, setRoadmapDefaults] = useState({
    title: "",
    description: "",
  });

  const [summarizingId, setSummarizingId] = useState<string | null>(null);
  const [summaryModalOpen, setSummaryModalOpen] = useState(false);
  const [summaryResult, setSummaryResult] = useState<SummarizeResult | null>(
    null
  );

  const bottomRef = useRef<HTMLDivElement>(null);

  const exchangeCount = useMemo(
    () => messages.filter((m) => m.id !== "welcome").length,
    [messages]
  );

  const canSummarize = Boolean(sessionId) && exchangeCount >= 4;

  const suggestions = useMemo(() => {
    const name = scopeLabel(scope, projects);
    return DEFAULT_SUGGESTIONS.map((s) =>
      s.includes("projet sélectionné")
        ? `Nouvelles features pour ${name}`
        : s
    );
  }, [scope, projects]);

  const loadSessions = useCallback(async () => {
    setSessionsLoading(true);
    try {
      setSessions(await fetchBrainstormSessions());
    } catch {
      setSessions([]); 
    } finally {
      setSessionsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProjects().then(setProjects).catch(() => setProjects([]));
    loadSessions();
  }, [loadSessions]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    if (!streamingId) return;
    const msg = messages.find((m) => m.id === streamingId);
    if (!msg) return;
    const words = msg.content.split(/\s+/).length;
    const duration = words * 18 + 300;
    const timer = setTimeout(() => setStreamingId(null), duration);
    return () => clearTimeout(timer);
  }, [streamingId, messages]);

  function handleScopeChange(next: ProjectScope, pid: string | null) {
    setScope(next);
    setProjectId(pid);
  }

  function startNewSession() {
    setSessionId(null);
    setMessages([]);
    setHasStarted(false);
    setInput("");
  }

  async function loadSession(id: string) {
    try {
      const data = await fetchBrainstormSession(id);
      setSessionId(data.session_id);
      setMessages(data.messages);
      setHasStarted(data.messages.some((m) => m.role === "user"));
      if (data.project_id) {
        setProjectId(data.project_id);
        setScope(data.project_id);
      } else {
        setProjectId(null);
        setScope(BRAINSTORM_GLOBAL_VALUE);
      }
    } catch {
      startNewSession();
    }
  }

  async function handleSend(text?: string) {
    const content = (text ?? input).trim();
    if (!content || loading) return;

    const userMsg: BrainstormMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content,
      created_at: new Date().toISOString(),
    };

    if (!hasStarted) {
      setHasStarted(true);
      setMessages([
        {
          id: "welcome",
          role: "assistant",
          content: WELCOME_MESSAGE,
          created_at: new Date().toISOString(),
        },
        userMsg,
      ]);
    } else {
      setMessages((prev) => [...prev, userMsg]);
    }

    setInput("");
    setLoading(true);

    try {
      const resolvedProjectId =
        scope === NEW_PROJECT_VALUE || scope === BRAINSTORM_GLOBAL_VALUE
          ? null
          : projectId;

      const { response, session_id } = await sendBrainstormMessage(
        content,
        resolvedProjectId,
        sessionId
      );

      if (!sessionId) setSessionId(session_id);

      const assistantMsg: BrainstormMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response,
        created_at: new Date().toISOString(),
      };

      setStreamingId(assistantMsg.id);
      setMessages((prev) => [...prev, assistantMsg]);
      loadSessions();
    } catch (err) {
      const detail =
        err instanceof Error ? err.message : "Erreur inconnue";
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: detail.includes("API ")
            ? "Impossible de joindre le Brainstorm Agent. Vérifie que l'API tourne sur le port 8000."
            : detail,
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function openRoadmapModal(content: string) {
    const firstLine = content.split("\n").find((l) => l.trim()) ?? content;
    setRoadmapDefaults({
      title: firstLine.replace(/^[\d\.\-\*]+\s*/, "").slice(0, 120),
      description: content.slice(0, 2000),
    });
    setRoadmapOpen(true);
  }

  async function handleSummarize(targetSessionId?: string) {
    const sid = targetSessionId ?? sessionId;
    if (!sid) return;

    const existing = sessions.find((s) => s.session_id === sid);
    if (existing?.has_summary && existing.summary_file_path) {
      try {
        const data = await fetchSessionSummary(sid);
        setSummaryResult({
          summary_md: data.summary,
          file_path: data.file_path ?? existing.summary_file_path,
          session_number: existing.summary_number ?? 0,
          title: data.title,
        });
        setSummaryModalOpen(true);
        return;
      } catch {
        /* regénérer si fetch échoue */
      }
    }

    setSummarizingId(sid);
    try {
      const result = await summarizeBrainstormSession(sid);
      setSummaryResult(result);
      setSummaryModalOpen(true);
      const slug = result.project_slug ?? "projet";
      toast.success(
        `Fiche #${String(result.session_number).padStart(3, "0")} sauvegardée dans brainstorm_notes/${slug}/`
      );
      loadSessions();
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Erreur lors de la synthèse"
      );
    } finally {
      setSummarizingId(null);
    }
  }

  const showEmpty = !hasStarted && messages.length === 0;

  return (
    <div className="flex h-full min-h-0 flex-1 flex-col">
      <div className="mb-3 flex shrink-0 flex-col gap-3 sm:mb-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-copper/70">
            Espace de réflexion
          </p>
          <h1 className="mt-1 text-xl font-medium text-ivory/90">Brainstorm</h1>
        </div>
        <ProjectSelector
          projects={projects}
          value={scope}
          onChange={handleScopeChange}
          onProjectsUpdated={setProjects}
          mode="brainstorm"
        />
      </div>

      <div className="flex min-h-0 flex-1 overflow-hidden rounded-2xl border border-copper/10 bg-obsidian/80 ring-1 ring-white/[0.04]">
        <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
          <div className="min-h-0 flex-1 overflow-hidden">
            {showEmpty ? (
              <BrainstormEmpty
                suggestions={suggestions}
                onSuggestionClick={(s) => handleSend(s)}
                layout="grid"
              />
            ) : (
              <ScrollArea className="h-full">
                <div className="mx-auto max-w-2xl space-y-6 px-4 py-6 sm:px-6">
                  {messages.map((msg) => (
                    <ChatMessageBubble
                      key={msg.id}
                      message={msg}
                      streaming={
                        msg.id === streamingId && msg.role === "assistant"
                      }
                      onAddRoadmap={
                        msg.role === "assistant" && msg.id !== "welcome"
                          ? openRoadmapModal
                          : undefined
                      }
                    />
                  ))}
                  {loading && (
                    <div className="flex items-center gap-2 text-xs text-titanium">
                      <Loader2 className="h-3.5 w-3.5 animate-spin text-copper" />
                      Réflexion en cours…
                    </div>
                  )}
                  <div ref={bottomRef} />
                </div>
              </ScrollArea>
            )}
          </div>

          <div className="relative z-10 shrink-0 border-t border-white/[0.06] bg-sidebar p-3 shadow-[0_-8px_24px_rgba(0,0,0,0.35)] sm:p-4">
            {canSummarize && (
              <div className="mx-auto mb-3 flex max-w-2xl justify-center">
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  disabled={Boolean(summarizingId)}
                  onClick={() => handleSummarize()}
                  className="border-copper/25 bg-copper/5 text-copper-glow hover:bg-copper/15"
                >
                  {summarizingId === sessionId ? (
                    <>
                      <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
                      Génération du compte-rendu…
                    </>
                  ) : (
                    <>
                      <FileText className="mr-2 h-3.5 w-3.5" />
                      Générer le compte-rendu
                    </>
                  )}
                </Button>
              </div>
            )}
            {!showEmpty && (
              <div className="mb-3 flex flex-wrap gap-1.5">
                {suggestions.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => handleSend(s)}
                    disabled={loading}
                    className="rounded-full border border-copper/15 px-2.5 py-1 text-[11px] text-titanium transition hover:border-copper/30 hover:text-copper-glow disabled:opacity-50"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
            <ChatInput
              input={input}
              loading={loading}
              onInputChange={setInput}
              onSend={() => handleSend()}
            />
          </div>
        </div>

        <SessionSidebar
          sessions={sessions}
          activeSessionId={sessionId}
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed((c) => !c)}
          onSelect={loadSession}
          onNewSession={startNewSession}
          onSummarize={handleSummarize}
          summarizingId={summarizingId}
          loading={sessionsLoading}
        />
      </div>

      <SummaryResultModal
        open={summaryModalOpen}
        onOpenChange={setSummaryModalOpen}
        result={summaryResult}
      />

      <RoadmapModal
        open={roadmapOpen}
        onOpenChange={setRoadmapOpen}
        defaultTitle={roadmapDefaults.title}
        defaultDescription={roadmapDefaults.description}
        defaultProjectId={projectId}
        projects={projects}
      />
    </div>
  );
}
