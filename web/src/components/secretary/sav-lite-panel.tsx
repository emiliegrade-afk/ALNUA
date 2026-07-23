"use client";

import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, Loader2, MessageSquare, RefreshCw, ShieldAlert } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import {
  approveSavCase,
  createSavCase,
  fetchSavCases,
  runSavWorkflow,
  syncSavKb,
  type SavCase,
} from "@/lib/sav-api";
import { cn } from "@/lib/utils";

const STATUS_LABEL: Record<string, string> = {
  open: "Ouvert",
  draft_ready: "Brouillon prêt",
  awaiting_ceo: "Validation CEO",
  replied: "Répondu",
  escalated: "Escaladé",
  closed: "Clôturé",
};

function statusBadge(status: string, needsCeo: boolean) {
  if (needsCeo || status === "awaiting_ceo") {
    return "border-amber-500/40 bg-amber-500/10 text-amber-200";
  }
  if (status === "draft_ready") {
    return "border-emerald-500/40 bg-emerald-500/10 text-emerald-200";
  }
  if (status === "replied") {
    return "border-copper/30 bg-copper/10 text-ivory/80";
  }
  return "border-titanium/20 bg-obsidian-3/80 text-titanium/70";
}

export function SavLitePanel() {
  const [cases, setCases] = useState<SavCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [productSlug, setProductSlug] = useState("hub");
  const [editReplies, setEditReplies] = useState<Record<string, string>>({});

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchSavCases();
      setCases(res.cases);
    } catch {
      setCases([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleSync() {
    setBusy("sync");
    try {
      const res = await syncSavKb();
      toast.success(`${res.synced} fiche(s) KB synchronisée(s)`);
      await load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Sync KB échouée");
    } finally {
      setBusy(null);
    }
  }

  async function handleWorkflow() {
    setBusy("workflow");
    try {
      const res = await runSavWorkflow();
      toast.success(res.summary?.slice(0, 120) || "Workflow SAV terminé");
      await load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Workflow SAV échoué");
    } finally {
      setBusy(null);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!subject.trim() || !body.trim()) return;
    setBusy("create");
    try {
      const res = await createSavCase({
        product_slug: productSlug,
        subject: subject.trim(),
        body: body.trim(),
      });
      if (!res.success) {
        toast.error(res.error || "Création cas échouée");
        return;
      }
      toast.success(
        res.needs_ceo
          ? "Cas créé — validation CEO requise"
          : "Brouillon Nadia prêt"
      );
      setSubject("");
      setBody("");
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur SAV");
    } finally {
      setBusy(null);
    }
  }

  async function handleApprove(c: SavCase) {
    setBusy(c.id);
    try {
      const reply = editReplies[c.id] ?? c.draft_reply ?? "";
      await approveSavCase(c.id, reply);
      toast.success("Réponse validée");
      await load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Validation échouée");
    } finally {
      setBusy(null);
    }
  }

  const pendingCeo = cases.filter(
    (c) => c.needs_ceo && c.status !== "replied" && c.status !== "closed"
  );

  return (
    <Card className="mb-8 border-copper/20 bg-obsidian-2/90">
      <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-4">
        <div>
          <CardTitle className="flex items-center gap-2 font-title text-base text-ivory">
            <MessageSquare className="h-4 w-4 text-copper" />
            SAV lite — Nadia
          </CardTitle>
          <p className="mt-1 font-body text-xs text-titanium/60">
            Brouillons auto · toi seule valides billing, plaintes et cas sensibles.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="border-copper/30"
            disabled={!!busy}
            onClick={() => void handleSync()}
          >
            {busy === "sync" ? (
              <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
            ) : (
              <RefreshCw className="mr-1 h-3.5 w-3.5" />
            )}
            Sync KB
          </Button>
          <Button
            type="button"
            size="sm"
            className="bg-copper/90 hover:bg-copper"
            disabled={!!busy}
            onClick={() => void handleWorkflow()}
          >
            {busy === "workflow" ? (
              <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
            ) : null}
            Run SAV
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {pendingCeo.length > 0 && (
          <div className="flex items-start gap-2 rounded-lg border border-amber-500/30 bg-amber-500/5 p-3 text-sm text-amber-100/90">
            <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" />
            <span>
              {pendingCeo.length} cas en attente de ta validation CEO
            </span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="grid gap-3 rounded-lg border border-titanium/10 p-4">
          <p className="label-caps text-titanium/50">Nouveau ticket test</p>
          <div className="flex flex-wrap gap-2">
            {["hub", "academy"].map((slug) => (
              <button
                key={slug}
                type="button"
                onClick={() => setProductSlug(slug)}
                className={cn(
                  "rounded-full px-3 py-1 text-xs font-medium transition",
                  productSlug === slug
                    ? "bg-copper/20 text-copper"
                    : "bg-obsidian-3 text-titanium/60 hover:text-ivory"
                )}
              >
                {slug}
              </button>
            ))}
          </div>
          <input
            className="rounded-md border border-titanium/15 bg-obsidian-3 px-3 py-2 text-sm text-ivory"
            placeholder="Objet"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
          />
          <Textarea
            placeholder="Message client"
            value={body}
            onChange={(e) => setBody(e.target.value)}
            rows={3}
            className="border-titanium/15 bg-obsidian-3 text-ivory"
          />
          <Button type="submit" size="sm" disabled={!!busy} className="w-fit">
            {busy === "create" ? (
              <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
            ) : null}
            Trier avec Nadia
          </Button>
        </form>

        {loading ? (
          <div className="flex items-center gap-2 text-sm text-titanium/50">
            <Loader2 className="h-4 w-4 animate-spin" />
            Chargement…
          </div>
        ) : cases.length === 0 ? (
          <p className="text-sm text-titanium/50">Aucun cas SAV pour l&apos;instant.</p>
        ) : (
          <ul className="space-y-3">
            {cases.map((c) => (
              <li
                key={c.id}
                className="rounded-lg border border-titanium/10 bg-obsidian-3/50 p-4"
              >
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <span className="font-medium text-ivory">{c.subject}</span>
                  <span
                    className={cn(
                      "rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-wide",
                      statusBadge(c.status, c.needs_ceo)
                    )}
                  >
                    {STATUS_LABEL[c.status] ?? c.status}
                  </span>
                  <span className="text-xs text-titanium/50">
                    {c.product_slug} · {c.category} · {Math.round((c.confidence || 0) * 100)}%
                  </span>
                </div>
                <p className="mb-3 line-clamp-2 text-xs text-titanium/60">{c.body}</p>
                {c.draft_reply && c.status !== "replied" && (
                  <div className="space-y-2">
                    <Textarea
                      value={editReplies[c.id] ?? c.draft_reply}
                      onChange={(e) =>
                        setEditReplies((prev) => ({ ...prev, [c.id]: e.target.value }))
                      }
                      rows={4}
                      className="border-titanium/15 bg-obsidian-2 text-sm text-ivory"
                    />
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      className="border-emerald-500/40 text-emerald-200"
                      disabled={busy === c.id}
                      onClick={() => void handleApprove(c)}
                    >
                      {busy === c.id ? (
                        <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <CheckCircle2 className="mr-1 h-3.5 w-3.5" />
                      )}
                      Valider la réponse
                    </Button>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
