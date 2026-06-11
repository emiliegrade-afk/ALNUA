"use client";

import { Sparkles, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface BriefingCardProps {
  briefing: string | null;
  loading: boolean;
  error?: string | null;
  onRefresh: () => void;
}

export function BriefingCard({
  briefing,
  loading,
  error,
  onRefresh,
}: BriefingCardProps) {
  const isInitialLoad = loading && !briefing;
  const isRefreshing = loading && !!briefing;
  return (
    <Card className="relative overflow-hidden border-copper/20 bg-surface/80 glow-copper backdrop-blur-sm">
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-copper/10 via-transparent to-transparent" />
      <CardHeader className="relative flex flex-row items-center justify-between pb-2">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-copper/20">
            <Sparkles className="h-4 w-4 text-copper" />
          </div>
          <div>
            <CardTitle className="text-base font-medium text-ivory">
              Briefing COO
            </CardTitle>
            <p className="text-xs text-titanium">Synthèse du jour</p>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onRefresh}
          disabled={loading}
          className="text-titanium/80 hover:text-ivory"
        >
          <RefreshCw
            className={cn(
              "mr-1.5 h-3.5 w-3.5",
              (isInitialLoad || isRefreshing) && "animate-spin"
            )}
          />
          {isRefreshing ? "Mise à jour…" : "Actualiser"}
        </Button>
      </CardHeader>
      <CardContent className="relative">
        {isInitialLoad ? (
          <div className="space-y-2">
            <Skeleton className="h-4 w-full bg-white/5" />
            <Skeleton className="h-4 w-4/5 bg-white/5" />
            <Skeleton className="h-4 w-3/5 bg-white/5" />
          </div>
        ) : briefing ? (
          <div className="space-y-2 text-sm leading-relaxed text-ivory/75 whitespace-pre-line">
            {briefing.split("\n").map((line, i) => (
              <p
                key={i}
                className="animate-fade-in"
                style={{ animationDelay: `${i * 60}ms` }}
              >
                {line}
              </p>
            ))}
          </div>
        ) : (
          <p className="text-sm text-titanium">
            {error ??
              "Briefing indisponible — vérifie que l'API FastAPI tourne sur le port 8000."}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
