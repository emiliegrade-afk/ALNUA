export type ProjectBranch = "app" | "gaming" | "robotics" | "other";
export type ProjectStatus = "active" | "beta" | "dev" | "paused";
export type AgentLogStatus = "success" | "error" | "pending";

export interface Project {
  id: string;
  name: string;
  branch: ProjectBranch;
  description: string;
  status: ProjectStatus;
  created_at: string;
}

export interface Ticket {
  id: string;
  project_id: string;
  type: string;
  priority: string;
  title: string;
  description: string;
  source: string;
  status: string;
  cursor_prompt: string | null;
  created_at: string;
  updated_at: string;
}

export interface AgentLog {
  id: string;
  agent_name: string;
  action: string;
  project_id: string | null;
  input_summary: string;
  output_summary: string;
  status: AgentLogStatus;
  created_at: string;
}

export interface ProjectWithStats extends Project {
  openTickets: number;
  criticalTickets: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export type RoadmapStatus = "idea" | "planned" | "in_progress" | "done";
export type RoadmapPriority = "critical" | "high" | "medium" | "low";

export interface RoadmapItem {
  id: string;
  project_id: string;
  title: string;
  description: string;
  status: RoadmapStatus;
  priority: RoadmapPriority;
  phase: string | null;
  due_date: string | null;
  linked_ticket_id: string | null;
  created_at: string;
  updated_at: string;
  project_name?: string;
}
