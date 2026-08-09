"use client";

import { useEffect, useState } from "react";
import { PLATFORM_STYLES, POST_STATUS_LABELS } from "@/components/content/content.constants";
import { fetchCalendar, type Post } from "@/lib/content";
import { C } from "@/app/app-v2/shared";
import { PremiumPanel, StatusPill } from "@/app/marketing-v2/premium";

/* "Aujourd'hui" — Vue Globale Marketing (Phase 38, échelle premium). Source
   réelle (fetchCalendar) — vue condensée d'une seule journée. */

function todayKey(): string {
  return new Date().toISOString().slice(0, 10);
}

function statusTone(status: Post["status"]): "done" | "progress" | "scheduled" {
  if (status === "published") return "done";
  if (status === "approved") return "progress";
  return "scheduled";
}

export function TodayContentPanel() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const today = todayKey();
    fetchCalendar({ dateFrom: today, dateTo: today })
      .then((res) => {
        if (!cancelled) setPosts(res.days[today] ?? []);
      })
      .catch(() => {
        if (!cancelled) setPosts([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const sorted = [...posts].sort((a, b) => a.scheduled_at.localeCompare(b.scheduled_at));

  return (
    <PremiumPanel title="Aujourd'hui">
      {loading && posts.length === 0 ? (
        <p className="text-[11px]" style={{ color: C.faint }}>
          Chargement…
        </p>
      ) : sorted.length === 0 ? (
        <p className="text-[11px]" style={{ color: C.faint }}>
          Aucune publication prévue aujourd&apos;hui.
        </p>
      ) : (
        <div className="flex flex-col">
          {sorted.map((post) => (
            <div key={post.id} className="flex items-start gap-3 border-b py-2.5 last:border-none last:pb-0" style={{ borderColor: C.line }}>
              <span className="w-10 shrink-0 pt-0.5 text-[10.5px]" style={{ color: C.faint }}>
                {new Date(post.scheduled_at).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <span
                    className="shrink-0 rounded px-[7px] py-[2px] text-[9.5px]"
                    style={{ background: "rgba(192,138,114,.12)", color: C.copperLight }}
                  >
                    {PLATFORM_STYLES[post.platform]?.label ?? post.platform}
                  </span>
                  <StatusPill tone={statusTone(post.status)}>{POST_STATUS_LABELS[post.status]}</StatusPill>
                </div>
                <p className="mt-1 truncate text-[11.5px]" style={{ color: C.warm }}>
                  {post.text_content}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </PremiumPanel>
  );
}
