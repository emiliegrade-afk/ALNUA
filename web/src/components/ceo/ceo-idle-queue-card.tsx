"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  CheckCircle2,
  FileText,
  Loader2,
  Play,
  RefreshCw,
  ListTodo,
  Ticket,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  fetchIdleDeliverable,
  fetchIdleDeliverables,
  fetchIdleQueue,
  promoteIdleTickets,
  runIdleDrain,
  runIdlePlan,
  validateIdleQueue,
  type IdleDayQueue,
  type IdleDeliverableSummary,
  type IdleQueueItem,
} from "@/lib/idle-work-api";
import { cn } from "@/lib/utils";

function levelTone(level: number): string {
  if (level >= 2) return "border-amber-500/30 bg-amber-500/10 text-amber-200";
  if (level >= 1) return "border-copper/25 bg-copper/10 text-copperLight";
  return "border-titanium/25 bg-titanium/10 text-titanium";
}

function ItemRow({
  item,
  onPreview,
}: {
  item: IdleQueueItem;
  onPreview: (id: string) => void;
}) {
  return (
    <li className="rounded-lg border border-copper/15 bg-obsidian-deep/40 px-3 py-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-sm text-ivory/90">{item.title}</span>
        <span
          className={cn(
            "rounded border px-1.5 py-0.5 text-[10px] font-medium",
            levelTone(item.level),
          )}
        >
          L{item.level} · {item.status}
        </span>
      </div>
      <div className="mt-1 flex flex-wrap items-center gap-2 text-[10px] text-titanium/55">
        <span>{item.agent_id}</span>
        <span>{item.kind}</span>
        <span>{item.family}</span>
        {item.run_id ? <span className="text-copper/80">run {item.run_id.slice(0, 12)}</span> : null}
        <button
          type="button"
          className="inline-flex items-center gap-1 text-copper hover:underline"
          onClick={() => onPreview(item.id)}
        >
          <FileText className="h-3 w-3" />
          Preview
        </button>
      </div>
      {item.detail ? (
        <p className="mt-1 truncate text-[10px] text-titanium/45">{item.detail}</p>
      ) : null}
    </li>
  );
}

export function CeoIdleQueueCard() {
  const [queue, setQueue] = useState<IdleDayQueue | null>(null);
  const [deliverables, setDeliverables] = useState<IdleDeliverableSummary[]>([]);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [q, d] = await Promise.all([fetchIdleQueue(), fetchIdleDeliverables(12)]);
      setQueue(q);
      setDeliverables(d);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "File idle indisponible");
      setQueue(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const counts = useMemo(() => {
    const items = queue?.items ?? [];
    return {
      total: items.length,
      pending: items.filter((i) => i.status === "pending").length,
      l2: items.filter((i) => i.level >= 2 && i.status === "pending").length,
      done: items.filter((i) => i.status === "done").length,
    };
  }, [queue]);

  async function withBusy(key: string, fn: () => Promise<void>) {
    setBusy(key);
    try {
      await fn();
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Action idle échouée");
    } finally {
      setBusy(null);
    }
  }

  async function handlePreview(itemId: string) {
    try {
      const data = await fetchIdleDeliverable(itemId);
      setPreview(JSON.stringify(data, null, 2));
    } catch {
      const hit = deliverables.find((d) => d.item_id === itemId);
      setPreview(hit?.preview ?? "Pas encore de livrable pour cet item — lance un drain.");
    }
  }

  return (
    <Card className="mb-8 border-copper/30 bg-obsidian-2/95">
      <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
        <div>
          <CardTitle className="flex items-center gap-2 font-title text-lg text-ivory">
            <ListTodo className="h-5 w-5 text-copper" />
            File du jour — Idle
          </CardTitle>
          <p className="mt-1 text-xs leading-relaxed text-titanium/65">
            L0–L1 auto · L2 après validation CEO (DEC-021)
            {queue?.date ? ` · ${queue.date}` : ""}
            {queue?.ceo_validated ? " · L2 ouvert" : ""}
          </p>
        </div>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => void load()}
          disabled={loading || busy != null}
          className="text-titanium/60"
        >
          <RefreshCw className={cn("h-3.5 w-3.5", loading && "animate-spin")} />
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {loading && !queue ? (
          <p className="text-sm text-titanium/50">Chargement…</p>
        ) : (
          <>
            <div className="flex flex-wrap items-center gap-3 text-xs text-titanium/70">
              <span>
                {counts.pending} en attente · {counts.done} faits · {counts.l2} L2
              </span>
              <span
                className={cn(
                  "rounded border px-2 py-0.5 text-[10px] font-semibold",
                  queue?.ceo_validated
                    ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
                    : "border-amber-500/30 bg-amber-500/10 text-amber-200",
                )}
              >
                {queue?.ceo_validated ? "L2 débloqué" : "L2 verrouillé"}
              </span>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button
                size="sm"
                variant="outline"
                className="border-copper/30 text-copper"
                disabled={busy != null}
                onClick={() =>
                  void withBusy("plan", async () => {
                    await runIdlePlan();
                    toast.success("File du jour reconstruite");
                  })
                }
              >
                {busy === "plan" ? (
                  <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                ) : (
                  <RefreshCw className="mr-1 h-3 w-3" />
                )}
                Replanifier
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="border-emerald-500/30 text-emerald-300"
                disabled={busy != null || !!queue?.ceo_validated}
                onClick={() =>
                  void withBusy("validate", async () => {
                    await validateIdleQueue(true);
                    toast.success("File validée — L2 autorisé");
                  })
                }
              >
                {busy === "validate" ? (
                  <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                ) : (
                  <CheckCircle2 className="mr-1 h-3 w-3" />
                )}
                Valider file (L2)
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="border-titanium/30 text-titanium"
                disabled={busy != null}
                onClick={() =>
                  void withBusy("drain", async () => {
                    const r = await runIdleDrain();
                    toast.success(
                      typeof r.summary === "string" ? r.summary : "Drain idle lancé",
                    );
                  })
                }
              >
                {busy === "drain" ? (
                  <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                ) : (
                  <Play className="mr-1 h-3 w-3" />
                )}
                Drain maintenant
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="border-copper/30 text-copperLight"
                disabled={busy != null}
                onClick={() =>
                  void withBusy("promote", async () => {
                    const r = await promoteIdleTickets({});
                    const n = Number(r.created_count ?? 0);
                    if (n > 0) toast.success(`${n} ticket(s) [idle-ok] créés`);
                    else if (r.project_id == null) {
                      toast.message("Aucun projet Hub — dry-run / tickets non créés");
                    } else toast.message("Aucun nouveau ticket (voir livrables)");
                  })
                }
              >
                {busy === "promote" ? (
                  <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                ) : (
                  <Ticket className="mr-1 h-3 w-3" />
                )}
                Créer tickets idle-ok
              </Button>
            </div>

            <ul className="space-y-2">
              {(queue?.items ?? []).slice(0, 12).map((item) => (
                <ItemRow key={item.id} item={item} onPreview={(id) => void handlePreview(id)} />
              ))}
              {(queue?.items?.length ?? 0) === 0 ? (
                <li className="text-xs text-titanium/45">
                  File vide — clique Replanifier ou attends le job 08:10.
                </li>
              ) : null}
            </ul>

            {deliverables.length > 0 ? (
              <div className="rounded-lg border border-copper/15 p-3">
                <p className="mb-2 text-xs font-medium text-titanium/50">Livrables récents</p>
                <ul className="space-y-1.5 text-xs text-titanium/70">
                  {deliverables.slice(0, 6).map((d) => (
                    <li key={d.item_id}>
                      <button
                        type="button"
                        className="text-left hover:text-copper"
                        onClick={() => void handlePreview(d.item_id)}
                      >
                        <span className="text-ivory/80">{d.title ?? d.item_id}</span>
                        {d.preview ? (
                          <span className="mt-0.5 block truncate text-[10px] text-titanium/45">
                            {d.preview}
                          </span>
                        ) : null}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {preview ? (
              <pre className="max-h-64 overflow-auto rounded-lg border border-copper/15 bg-obsidian-deep/60 p-3 text-[10px] text-titanium/80 whitespace-pre-wrap">
                {preview}
              </pre>
            ) : null}
          </>
        )}
      </CardContent>
    </Card>
  );
}
