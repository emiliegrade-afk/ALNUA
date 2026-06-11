"use client";

import Link from "next/link";
import { ArrowUpRight, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  BRANCH_LABELS,
  getProjectAccent,
  getStatusDotClass,
  getStatusLabel,
} from "@/lib/projects";
import type { ProjectWithStats } from "@/lib/types";
import { cn } from "@/lib/utils";

interface ProjectCardsProps {
  projects: ProjectWithStats[];
  loading?: boolean;
}

export function ProjectCards({ projects, loading }: ProjectCardsProps) {
  if (loading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <Card
            key={i}
            className="h-40 animate-pulse border-white/[0.06] bg-surface"
          />
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {projects.map((project, index) => {
        const accent = getProjectAccent(project.branch);
        return (
          <Link key={project.id} href={`/tickets?project=${project.id}`}>
            <Card
              className={cn(
                "group relative h-full overflow-hidden border bg-surface/80 transition-all duration-300 hover:-translate-y-0.5 hover:border-white/15",
                accent.border,
                accent.glow
              )}
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div
                className={cn(
                  "pointer-events-none absolute inset-0 bg-gradient-to-br opacity-60",
                  accent.gradient
                )}
              />
              <CardContent className="relative p-5">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <span
                      className={cn("status-dot", getStatusDotClass(project.status))}
                    />
                    <Badge
                      variant="outline"
                      className={cn(
                        "border-0 text-[10px] uppercase tracking-wider",
                        accent.bg,
                        accent.color
                      )}
                    >
                      {BRANCH_LABELS[project.branch]}
                    </Badge>
                  </div>
                  <ArrowUpRight className="h-4 w-4 text-titanium/60 transition group-hover:text-ivory/75" />
                </div>

                <h3 className="mt-4 text-lg font-semibold text-ivory">
                  {project.name}
                </h3>
                <p className="mt-1 line-clamp-2 text-xs text-titanium">
                  {project.description}
                </p>

                <div className="mt-5 flex items-end justify-between">
                  <div>
                    <p className="text-2xl font-semibold tabular-nums text-ivory">
                      {project.openTickets}
                    </p>
                    <p className="text-[11px] text-titanium">tickets ouverts</p>
                  </div>
                  <div className="text-right">
                    <Badge
                      variant="secondary"
                      className="bg-white/[0.06] text-ivory/75"
                    >
                      {getStatusLabel(project.status)}
                    </Badge>
                    {project.criticalTickets > 0 && (
                      <p className="mt-1.5 flex items-center justify-end gap-1 text-[11px] text-amber-400">
                        <AlertTriangle className="h-3 w-3" />
                        {project.criticalTickets} critique
                        {project.criticalTickets > 1 ? "s" : ""}
                      </p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </Link>
        );
      })}
    </div>
  );
}
