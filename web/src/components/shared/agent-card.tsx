"use client";

import { Bot } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DEPT_COLORS, type DeptKey } from "@/lib/dept-colors";
import { useCooStore } from "@/store/coo-store";
import { cn } from "@/lib/utils";

export interface AgentCardProps {
  icon?: string;
  name: string;
  role: string;
  branch: DeptKey;
  description: string;
  skills: string[];
  badge?: string;
  status?: "idle" | "working" | "waiting" | "error";
  currentTask?: string;
  onClick?: () => void;
  onDelegate?: () => void;
}

export function AgentCard({
  icon,
  name,
  role,
  branch,
  description,
  skills,
  badge,
  status,
  currentTask,
  onClick,
  onDelegate,
}: AgentCardProps) {
  const setPrefillMessage = useCooStore((s) => s.setPrefillMessage);
  const openDrawer = useCooStore((s) => s.openDrawer);
  const colors = DEPT_COLORS[branch];

  function handleDelegate() {
    if (onDelegate) {
      onDelegate();
      return;
    }
    setPrefillMessage(`Délègue une tâche à ${name} (${role}) : `);
    openDrawer();
  }

  return (
    <div>
    <Card
      className={cn(
        "border-copper/20 bg-obsidian-2/90 backdrop-blur-sm transition-all duration-300 hover:border-copper/40 hover:shadow-copper-glow",
        onClick && "cursor-pointer",
      )}
      style={{ borderColor: colors.border }}
      onClick={onClick}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-3">
            <div
              className="flex h-10 w-10 items-center justify-center rounded-lg text-lg"
              style={{ backgroundColor: colors.bg }}
            >
              {icon ? (
                <span className="text-xl leading-none">{icon}</span>
              ) : (
                <Bot className="h-5 w-5" style={{ color: colors.main }} />
              )}
            </div>
            <div>
              <CardTitle className="font-title text-base text-ivory">
                {name}
              </CardTitle>
              <p className="font-body text-xs" style={{ color: colors.main }}>
                {role}
              </p>
            </div>
          </div>
          {badge ? (
            <span
              className="badge-copper shrink-0 px-2 py-1 text-[10px] font-medium"
              style={{ backgroundColor: colors.bg, color: colors.main }}
            >
              {badge}
            </span>
          ) : null}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="font-body text-sm text-titanium">{description}</p>
        <div className="flex flex-wrap gap-1.5">
          {skills.map((skill) => (
            <span
              key={skill}
              className={cn(
                "rounded-full px-2 py-0.5 font-body text-[11px] text-titanium ring-1 ring-copper/10"
              )}
            >
              {skill}
            </span>
          ))}
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            handleDelegate();
          }}
          className="w-full border-copper/30 font-body text-titanium hover:border-copper/50 hover:bg-copper/5 hover:text-ivory"
        >
          Déléguer une tâche
        </Button>
      </CardContent>
    </Card>
    {status === "working" && (
      <div className="mt-2 flex items-center gap-2 text-xs text-copper animate-pulse">
        <span className="h-1.5 w-1.5 rounded-full bg-copper" />
        {currentTask ?? "En train de coder..."}
      </div>
    )}
    {status === "idle" && (
      <div className="mt-2 flex items-center gap-2 text-xs text-titanium/40">
        <span className="h-1.5 w-1.5 rounded-full bg-titanium/20" />
        Inactif
      </div>
    )}
    </div>
  );
}
