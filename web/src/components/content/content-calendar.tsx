"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { format, addDays, startOfWeek } from "date-fns";
import { fr } from "date-fns/locale";
import { ChevronLeft, ChevronRight } from "lucide-react";
import {
  PLATFORM_STYLES,
  SECTORS,
  SECTOR_STYLES,
  type ContentSector,
} from "@/components/content/content.constants";
import { PostEditModal } from "@/components/content/post-edit-modal";
import { Button } from "@/components/ui/button";
import { fetchCalendar, type Post } from "@/lib/content";
import { cn } from "@/lib/utils";

function toDateKey(d: Date): string {
  return format(d, "yyyy-MM-dd");
}

interface ContentCalendarProps {
  onPostUpdated: (post: Post) => void;
}

export function ContentCalendar({ onPostUpdated }: ContentCalendarProps) {
  const [weekStart, setWeekStart] = useState(() =>
    startOfWeek(new Date(), { weekStartsOn: 1 })
  );
  const [sectorFilter, setSectorFilter] = useState<ContentSector | null>(null);
  const [days, setDays] = useState<Record<string, Post[]>>({});
  const [loading, setLoading] = useState(true);
  const [editingPost, setEditingPost] = useState<Post | null>(null);

  const weekDays = useMemo(
    () => Array.from({ length: 7 }, (_, i) => addDays(weekStart, i)),
    [weekStart]
  );

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const result = await fetchCalendar({
        dateFrom: toDateKey(weekStart),
        dateTo: toDateKey(addDays(weekStart, 6)),
        sector: sectorFilter ?? undefined,
      });
      setDays(result.days);
    } catch {
      setDays({});
    } finally {
      setLoading(false);
    }
  }, [weekStart, sectorFilter]);

  useEffect(() => {
    load();
  }, [load]);

  function handleSaved(post: Post) {
    onPostUpdated(post);
    load();
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8 border-copper/20 bg-obsidian-deep/50"
            onClick={() => setWeekStart((d) => addDays(d, -7))}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <p className="min-w-[200px] text-center text-sm text-ivory/85">
            {format(weekStart, "d MMM", { locale: fr })} –{" "}
            {format(addDays(weekStart, 6), "d MMM yyyy", { locale: fr })}
          </p>
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8 border-copper/20 bg-obsidian-deep/50"
            onClick={() => setWeekStart((d) => addDays(d, 7))}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 text-xs text-titanium"
            onClick={() => setWeekStart(startOfWeek(new Date(), { weekStartsOn: 1 }))}
          >
            Aujourd&apos;hui
          </Button>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {SECTORS.map(({ id, label }) => {
            const active = sectorFilter === id;
            return (
              <button
                key={id}
                type="button"
                onClick={() => setSectorFilter(active ? null : id)}
                className={cn(
                  "rounded-md px-2 py-1 text-[10px] ring-1 transition",
                  active
                    ? SECTOR_STYLES[id]
                    : "bg-obsidian-deep/50 text-titanium ring-copper/15 hover:ring-copper/20"
                )}
              >
                {label}
              </button>
            );
          })}
        </div>
      </div>

      {loading ? (
        <p className="py-12 text-center text-sm text-titanium">Chargement du calendrier…</p>
      ) : (
        <div className="grid flex-1 grid-cols-1 gap-2 overflow-y-auto sm:grid-cols-2 lg:grid-cols-7">
          {weekDays.map((day) => {
            const key = toDateKey(day);
            const posts = days[key] ?? [];
            const isToday = key === toDateKey(new Date());
            return (
              <div
                key={key}
                className={cn(
                  "flex min-h-[140px] flex-col gap-1.5 rounded-xl border p-2",
                  isToday
                    ? "border-copper/40 bg-copper/5"
                    : "border-copper/10 bg-obsidian-deep/40"
                )}
              >
                <p
                  className={cn(
                    "text-[11px] font-medium uppercase tracking-wide",
                    isToday ? "text-copper-glow" : "text-titanium"
                  )}
                >
                  {format(day, "EEE d", { locale: fr })}
                </p>
                <div className="flex flex-1 flex-col gap-1.5">
                  {posts.length === 0 ? (
                    <p className="mt-2 text-center text-[10px] text-titanium/50">—</p>
                  ) : (
                    posts.map((post) => {
                      const platformStyle = PLATFORM_STYLES[post.platform];
                      return (
                        <button
                          key={post.id}
                          type="button"
                          onClick={() => setEditingPost(post)}
                          className={cn(
                            "rounded-lg px-2 py-1.5 text-left text-[11px] ring-1 transition hover:brightness-110",
                            platformStyle?.badge ?? "bg-obsidian-deep/50 text-titanium ring-copper/15"
                          )}
                        >
                          <p className="line-clamp-2 leading-snug">{post.text_content}</p>
                          <p className="mt-0.5 text-[9px] opacity-70">
                            {format(new Date(post.scheduled_at), "HH:mm")} · {post.status}
                          </p>
                        </button>
                      );
                    })
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      <PostEditModal
        post={editingPost}
        open={!!editingPost}
        onOpenChange={(open) => !open && setEditingPost(null)}
        onSaved={handleSaved}
      />
    </div>
  );
}
