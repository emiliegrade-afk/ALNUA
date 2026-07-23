import type { LucideIcon } from "lucide-react";

export type ConsoleAgentStatus = "active" | "thinking" | "idle" | "review";

export interface ConsoleAgent {
  id: string;
  name: string;
  role: string;
  specialty: string;
  status: ConsoleAgentStatus;
  model: string;
  utilization: number;
  task: string;
  initials: string;
  hue: string;
}

export interface ConsoleDepartment {
  id: string;
  code: string;
  name: string;
  tagline: string;
  description: string;
  href: string;
  icon: LucideIcon;
  accent: string;
  ring: string;
  glow: string;
  agents: ConsoleAgent[];
  kpis: { label: string; value: string }[];
  projects: { name: string; progress: number; status: "on-track" | "review" | "r&d" }[];
}

export type ActivityKind = "ship" | "decide" | "research" | "alert" | "create";

export interface ConsoleActivityItem {
  id: string;
  kind: ActivityKind;
  agent: string;
  dept: string;
  action: string;
  time: string;
}

export interface ConsoleGlobalKpi {
  label: string;
  value: string;
  unit?: string;
  delta: string;
  trend: number[];
}
