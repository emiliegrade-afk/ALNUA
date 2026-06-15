"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2, MessageSquare, Plus, Send, Users, XCircle, FileText } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  closeCommitteeSession,
  generateCommitteeReport,
  sendCommitteeMessage,
  startCommitteeSession,
  type CommitteeMember,
  type CommitteeMessage,
  type CommitteeSession,
} from "@/lib/rnd-dossier";
import { cn } from "@/lib/utils";

const MEMBER_STYLES: Record<string, string> = {
  pm: "border-copper/30 bg-copper/10 text-copper",
  spec: "border-blue-500/25 bg-blue-500/10 text-blue-300",
  marketing: "border-pink-500/25 bg-pink-500/10 text-pink-300",
  accounting: "border-emerald-500/25 bg-emerald-500/10 text-emerald-300",
  dev_app: "border-violet-500/25 bg-violet-500/10 text-violet-300",
  content: "border-amber-500/25 bg-amber-500/10 text-amber-200",
  default: "border-white/15 bg-white/[0.04] text-ivory/80",
};

function speakerLabel(speaker: string, team: CommitteeMember[]): string {
  const m = team.find((t) => t.id === speaker);
  if (m) return `${m.emoji} ${m.name}`;
  if (speaker === "system") return "Système";
  if (speaker === "emilie") return "Emilie";
  return speaker;
}

function CommitteeBubble({
  msg,
  team,
}: {
  msg: CommitteeMessage;
  team: CommitteeMember[];
}) {
  const isUser = msg.role === "user";
  const isSystem = msg.role === "system";
  const style = MEMBER_STYLES[msg.speaker] ?? MEMBER_STYLES.default;

  return (
    <div
      className={cn(
        "flex flex-col gap-1",
        isUser ? "items-end" : "items-start"
      )}
    >
      <span className="text-[10px] text-titanium/50">
        {speakerLabel(msg.speaker, team)}
      </span>
      <div
        className={cn(
          "max-w-[92%] rounded-xl px-3 py-2 text-sm leading-relaxed",
          isUser
            ? "bg-copper/20 text-ivory/95"
            : isSystem
              ? "border border-white/10 bg-white/[0.03] text-titanium/70 italic"
              : cn("border", style)
        )}
      >
        <p className="whitespace-pre-wrap">{msg.content}</p>
      </div>
    </div>
  );
}

interface RndCommitteePanelProps {
  dossierId: string;
  dossierTitle: string;
  activeSection?: string | null;
  onClosed?: () => void;
}

export function RndCommitteePanel({
  dossierId,
  dossierTitle,
  activeSection,
  onClosed,
}: RndCommitteePanelProps) {
  const [session, setSession] = useState<CommitteeSession | null>(null);
  const [messages, setMessages] = useState<CommitteeMessage[]>([]);
  const [readOnly, setReadOnly] = useState(false);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [closing, setClosing] = useState(false);
  const [reporting, setReporting] = useState(false);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const start = useCallback(async (forceNew = false) => {
    setLoading(true);
    try {
      const data = await startCommitteeSession(dossierId, {
        active_section: activeSection ?? undefined,
        force_new: forceNew,
      });
      setSession(data.session);
      setMessages(data.messages);
      setReadOnly(Boolean(data.read_only));
      if (!data.resumed) {
        toast.success("Comité R&D ouvert");
      } else if (data.read_only) {
        toast.info("Historique de la dernière session comité");
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Impossible d'ouvrir le comité");
    } finally {
      setLoading(false);
    }
  }, [dossierId, activeSection]);

  useEffect(() => {
    void start(false);
  }, [start]);

  async function handleNewSession() {
    await start(true);
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function handleSend() {
    if (!session || !input.trim() || sending) return;
    setSending(true);
    const text = input.trim();
    setInput("");
    try {
      const data = await sendCommitteeMessage(dossierId, session.session_id, text);
      setMessages((prev) => [
        ...prev,
        data.user_message,
        ...data.responses,
      ]);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Envoi impossible");
      setInput(text);
    } finally {
      setSending(false);
    }
  }

  async function handleGenerateReport() {
    if (!session || reporting || session.status === "closed") return;
    setReporting(true);
    try {
      const result = await generateCommitteeReport(dossierId, session.session_id);
      toast.success("Compte-rendu structuré généré");
      if (result.message) {
        setMessages((prev) => [...prev, result.message]);
      } else if (result.committee_report_md) {
        setMessages((prev) => [
          ...prev,
          {
            id: `report-${Date.now()}`,
            session_id: session.session_id,
            dossier_id: dossierId,
            speaker: "pm",
            role: "assistant",
            content: result.committee_report_md,
            metadata: { committee_report: true, on_demand: true },
          },
        ]);
      }
      onClosed?.();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Génération CR impossible");
    } finally {
      setReporting(false);
    }
  }

  async function handleClose() {
    if (!session || closing) return;
    setClosing(true);
    try {
      const result = await closeCommitteeSession(dossierId, session.session_id, {
        generateCeoPackage: true,
      });
      const ceoMsg = result.ceo_package?.message;
      const status = result.dossier_status;
      if (ceoMsg) {
        toast.success(`Comité clos — ${ceoMsg}`, { duration: 6000 });
      } else if (result.ceo_package_error) {
        toast.warning(
          `Comité clos (${status}) — dossier CEO non généré : ${result.ceo_package_error}`,
          { duration: 8000 }
        );
      } else if (result.sections_updated.length > 0) {
        toast.success(
          `Comité clos — ${result.sections_updated.length} section(s) mises à jour · statut ${status}`
        );
      } else {
        toast.success(`Comité clos — CR enregistré · statut ${status}`);
      }
      if (result.synthesis_md) {
        setMessages((prev) => [
          ...prev,
          {
            id: `synthesis-${Date.now()}`,
            session_id: session.session_id,
            dossier_id: dossierId,
            speaker: "pm",
            role: "assistant",
            content: result.synthesis_md,
            metadata: { synthesis: true },
          },
        ]);
      }
      setSession((s) => (s ? { ...s, status: "closed" } : s));
      setReadOnly(true);
      onClosed?.();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Clôture impossible");
    } finally {
      setClosing(false);
    }
  }

  if (loading && !session) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-copper/50" />
      </div>
    );
  }

  const team = session?.team ?? [];
  const isClosed = session?.status === "closed" || readOnly;

  return (
    <div className="flex h-full min-h-[420px] flex-col rounded-xl border border-copper/15 bg-copper/[0.02]">
      <div className="flex shrink-0 items-center justify-between gap-2 border-b border-copper/10 px-4 py-3">
        <div>
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-copper" />
            <h3 className="text-sm font-semibold text-ivory/90">Comité R&D</h3>
          </div>
          <p className="text-[10px] text-titanium/50">{dossierTitle}</p>
        </div>
        <div className="flex items-center gap-2">
          {isClosed ? (
            <>
              <span className="text-[10px] text-titanium/50">Session fermée</span>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={loading}
                onClick={() => void handleNewSession()}
                className="border-copper/30 text-copper hover:bg-copper/10"
              >
                {loading ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <Plus className="mr-1 h-3 w-3" />
                )}
                Nouvelle session
              </Button>
            </>
          ) : (
            <>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={reporting || closing}
                onClick={() => void handleGenerateReport()}
                className="border-copper/30 text-copper hover:bg-copper/10"
              >
                {reporting ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <FileText className="mr-1 h-3 w-3" />
                )}
                Générer le CR
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={closing || reporting}
                onClick={() => void handleClose()}
                className="border-red-500/30 text-red-300 hover:bg-red-500/10"
              >
                {closing ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <XCircle className="mr-1 h-3 w-3" />
                )}
                Clôturer
              </Button>
            </>
          )}
        </div>
      </div>

      {isClosed ? (
        <p className="shrink-0 border-b border-copper/10 bg-amber-500/[0.06] px-4 py-2 text-[11px] text-amber-200/80">
          Historique conservé — le dossier CEO est dans l&apos;onglet{" "}
          <strong className="font-normal text-ivory/85">Dossier CEO</strong>. Ouvre une
          nouvelle session pour reprendre le débat.
        </p>
      ) : null}

      {team.length > 0 ? (
        <div className="flex shrink-0 flex-wrap gap-1.5 border-b border-copper/10 px-4 py-2">
          {team.map((m) => (
            <span
              key={m.id}
              className="rounded-full border border-white/10 bg-white/[0.03] px-2 py-0.5 text-[10px] text-titanium/70"
              title={m.title}
            >
              {m.emoji} {m.name}
            </span>
          ))}
        </div>
      ) : null}

      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto px-4 py-3">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-center text-sm text-titanium/50">
            <MessageSquare className="h-8 w-8 text-copper/20" />
            <p>Le comité va prendre la parole…</p>
          </div>
        ) : (
          messages.map((msg) => (
            <CommitteeBubble key={msg.id} msg={msg} team={team} />
          ))
        )}
        {sending ? (
          <div className="flex items-center gap-2 text-xs text-titanium/50">
            <Loader2 className="h-3 w-3 animate-spin" />
            Les agents répondent…
          </div>
        ) : null}
        <div ref={bottomRef} />
      </div>

      {!isClosed ? (
        <form
          className="flex shrink-0 gap-2 border-t border-copper/10 p-3"
          onSubmit={(e) => {
            e.preventDefault();
            void handleSend();
          }}
        >
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Challenge le dossier… @marketing @compta"
            rows={2}
            disabled={sending}
            className="min-h-[48px] resize-none border-copper/15 bg-white/[0.02] text-sm"
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void handleSend();
              }
            }}
          />
          <Button
            type="submit"
            disabled={sending || !input.trim()}
            className="h-auto shrink-0 bg-copper px-3 hover:bg-copper/90"
          >
            <Send className="h-4 w-4" />
          </Button>
        </form>
      ) : null}
    </div>
  );
}
