"use client";

import { useCallback, useEffect, useState } from "react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import { ChevronDown, ChevronUp, Loader2, RefreshCw, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  clearEventStore,
  fetchEventStats,
  fetchEventTypes,
  fetchRecentEvents,
  type EventStats,
  type HubEvent,
} from "@/lib/admin-events-api";
import { cn } from "@/lib/utils";

function EventRow({ event }: { event: HubEvent }) {
  const [open, setOpen] = useState(false);
  const when = event.ts
    ? format(new Date(event.ts * 1000), "dd MMM HH:mm:ss", { locale: fr })
    : "—";

  return (
    <div className="rounded-lg border border-copper/10 bg-obsidian/60 p-3">
      <button
        type="button"
        className="flex w-full items-start justify-between gap-2 text-left"
        onClick={() => setOpen((v) => !v)}
      >
        <div>
          <p className="font-body text-sm text-ivory">
            <span className="text-copper-light">{event.event_type}</span>
            {event.source_agent ? (
              <span className="text-titanium/60"> · {event.source_agent}</span>
            ) : null}
          </p>
          <p className="mt-0.5 font-body text-xs text-titanium/50">{when}</p>
        </div>
        {open ? (
          <ChevronUp className="h-4 w-4 shrink-0 text-titanium/50" />
        ) : (
          <ChevronDown className="h-4 w-4 shrink-0 text-titanium/50" />
        )}
      </button>
      {open && (
        <pre className="mt-3 max-h-48 overflow-auto rounded bg-obsidian-2 p-2 font-mono text-xs text-titanium/80">
          {JSON.stringify(event.payload, null, 2)}
        </pre>
      )}
    </div>
  );
}

export function AdminEventsView() {
  const [events, setEvents] = useState<HubEvent[]>([]);
  const [stats, setStats] = useState<EventStats | null>(null);
  const [types, setTypes] = useState<Record<string, string>>({});
  const [filterType, setFilterType] = useState("");
  const [loading, setLoading] = useState(true);
  const [clearing, setClearing] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [recent, statsData, typesData] = await Promise.all([
        fetchRecentEvents({
          eventType: filterType || undefined,
          limit: 50,
        }),
        fetchEventStats(),
        fetchEventTypes(),
      ]);
      setEvents(recent);
      setStats(statsData);
      setTypes(typesData);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur event bus");
      setEvents([]);
      setStats(null);
    } finally {
      setLoading(false);
    }
  }, [filterType]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleClear() {
    if (!window.confirm("Vider le store mémoire des events ? (logs disque conservés)")) {
      return;
    }
    setClearing(true);
    try {
      await clearEventStore();
      toast.success("Store events vidé");
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur");
    } finally {
      setClearing(false);
    }
  }

  const topTypes = stats
    ? Object.entries(stats.by_type).slice(0, 8)
    : [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end gap-4">
        <div className="min-w-[200px] flex-1">
          <Label htmlFor="event-filter" className="text-titanium/70">
            Filtrer par type
          </Label>
          <Input
            id="event-filter"
            list="event-types"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            placeholder="task_completed, budget_alert…"
            className="mt-1 border-copper/20 bg-obsidian-2"
          />
          <datalist id="event-types">
            {Object.keys(types).map((t) => (
              <option key={t} value={t} />
            ))}
          </datalist>
        </div>
        <Button
          type="button"
          variant="outline"
          className="border-copper/30"
          onClick={() => void load()}
          disabled={loading}
        >
          <RefreshCw className={cn("mr-2 h-4 w-4", loading && "animate-spin")} />
          Actualiser
        </Button>
        <Button
          type="button"
          variant="outline"
          className="border-red-500/30 text-red-300 hover:bg-red-500/10"
          onClick={() => void handleClear()}
          disabled={clearing}
        >
          <Trash2 className="mr-2 h-4 w-4" />
          Vider store
        </Button>
      </div>

      {stats && (
        <div className="grid gap-4 sm:grid-cols-3">
          <Card className="border-copper/20 bg-obsidian-2/80">
            <CardContent className="pt-6">
              <p className="text-xs text-titanium/60">En mémoire</p>
              <p className="font-title text-2xl text-ivory">
                {stats.total_events_in_memory}
              </p>
            </CardContent>
          </Card>
          <Card className="border-copper/20 bg-obsidian-2/80 sm:col-span-2">
            <CardContent className="pt-6">
              <p className="mb-2 text-xs text-titanium/60">Top types</p>
              <div className="flex flex-wrap gap-2">
                {topTypes.map(([type, count]) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => setFilterType(type)}
                    className="rounded-full border border-copper/20 px-2.5 py-0.5 font-body text-xs text-titanium hover:border-copper/40"
                  >
                    {type} ({count})
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <Card className="border-copper/20 bg-obsidian-2/80">
        <CardHeader>
          <CardTitle className="font-title text-base text-ivory">Timeline</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {loading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-copper/60" />
            </div>
          ) : events.length === 0 ? (
            <p className="font-body text-sm text-titanium/60">
              Aucun event récent. Les handlers émettent via{" "}
              <code className="text-copper-light">emit()</code> après les tâches agents.
            </p>
          ) : (
            events.map((ev) => <EventRow key={ev.event_id} event={ev} />)
          )}
        </CardContent>
      </Card>
    </div>
  );
}
