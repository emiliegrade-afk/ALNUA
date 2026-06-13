"use client";

import Link from "next/link";
import { ArrowUpRight, Star } from "lucide-react";
import {
  FEEDBACK_SOURCE_LABELS,
} from "@/components/analytics/analytics.constants";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getProjectAccent } from "@/lib/projects";
import type { FeedbackRow } from "@/lib/analytics";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";

interface RecentFeedbackTableProps {
  feedback: FeedbackRow[];
  projects: Project[];
}

function RatingStars({ rating }: { rating: number | null }) {
  if (rating == null) {
    return <span className="text-xs text-titanium/50">–</span>;
  }
  return (
    <span className="inline-flex items-center gap-0.5">
      {Array.from({ length: 5 }).map((_, i) => (
        <Star
          key={i}
          className={cn(
            "h-3 w-3",
            i < rating
              ? "fill-amber-400 text-amber-400"
              : "text-white/15"
          )}
        />
      ))}
    </span>
  );
}

export function RecentFeedbackTable({ feedback, projects }: RecentFeedbackTableProps) {
  const recent = feedback.slice(0, 5);
  const projectMap = Object.fromEntries(projects.map((p) => [p.id, p]));

  return (
    <Card className="border-white/[0.06] bg-surface/80">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-ivory">
          Derniers avis
        </CardTitle>
        <Link
          href="/beta"
          className="flex items-center gap-1 text-xs text-copper-glow hover:underline"
        >
          Voir tous
          <ArrowUpRight className="h-3 w-3" />
        </Link>
      </CardHeader>
      <CardContent className="p-0">
        {recent.length === 0 ? (
          <p className="px-4 pb-4 text-sm text-titanium/60">
            Aucun avis pour le moment.
          </p>
        ) : (
          <div className="divide-y divide-white/[0.06]">
            {recent.map((item) => {
              const project = projectMap[item.project_id];
              const accent = getProjectAccent(project?.branch ?? "other");

              return (
                <div
                  key={item.id}
                  className="grid gap-2 px-4 py-3 sm:grid-cols-[auto_1fr_auto] sm:items-center"
                >
                  <RatingStars rating={item.rating} />
                  <div className="min-w-0">
                    <p className="line-clamp-2 text-sm text-ivory/90">
                      {item.content}
                    </p>
                    <p className="mt-1 text-[11px] text-titanium/70">
                      {FEEDBACK_SOURCE_LABELS[item.source] ?? item.source}
                    </p>
                  </div>
                  <span
                    className={cn(
                      "shrink-0 self-start rounded-md px-2 py-0.5 text-[10px] sm:self-center",
                      accent.bg,
                      accent.color
                    )}
                  >
                    {project?.name ?? item.project_name ?? "Projet"}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
