"use client";

import { useRouter } from "next/navigation";
import { Bot } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DEPT_COLORS } from "@/lib/dept-colors";
import { useCooStore } from "@/store/coo-store";
import { cn } from "@/lib/utils";

export interface AgentCardProps {
  icon?: string;
  name: string;
  role: string;
  branch: "hub" | "app" | "gaming" | "robo" | "marketing" | "rd";
  description: string;
  skills: string[];
  badge?: string;
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
  onDelegate,
}: AgentCardProps) {
  const router = useRouter();
  const setPrefillMessage = useCooStore((s) => s.setPrefillMessage);
  const colors = DEPT_COLORS[branch];

  function handleDelegate() {
    if (onDelegate) {
      onDelegate();
      return;
    }
    setPrefillMessage(`Délègue une tâche à ${name} (${role}) : `);
    router.push("/ceo");
  }

  return (
    <Card
      className="border-white/[0.08] bg-[#111827]/80 backdrop-blur-sm"
      style={{ borderColor: colors.border }}
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
              <CardTitle className="text-base text-white">{name}</CardTitle>
              <p className="text-xs" style={{ color: colors.main }}>
                {role}
              </p>
            </div>
          </div>
          {badge ? (
            <span
              className="shrink-0 rounded-full px-2 py-1 text-[10px] font-medium"
              style={{ backgroundColor: colors.bg, color: colors.main }}
            >
              {badge}
            </span>
          ) : null}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-gray-400">{description}</p>
        <div className="flex flex-wrap gap-1.5">
          {skills.map((skill) => (
            <span
              key={skill}
              className={cn(
                "rounded-full px-2 py-0.5 text-[11px] ring-1 ring-white/10 text-gray-400"
              )}
            >
              {skill}
            </span>
          ))}
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleDelegate}
          className="w-full border-white/10 text-gray-300 hover:bg-white/5"
          style={{ borderColor: colors.border }}
        >
          Déléguer une tâche
        </Button>
      </CardContent>
    </Card>
  );
}
