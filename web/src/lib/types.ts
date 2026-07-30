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
  assignee_agent_id: string | null;
  story_points: number | null;
  due_date: string | null;
  created_at: string;
  updated_at: string;
}

export type ModuleStatus = "a_faire" | "en_developpement" | "en_test" | "termine";

export interface ProjectModule {
  id: string;
  project_id: string;
  name: string;
  status: ModuleStatus;
  progress: number;
  features_done: number;
  features_total: number;
  tests_passed_pct: number;
  open_bugs: number;
  position: number;
  created_at: string;
  updated_at: string;
}

export type GamingBuildStatus = "success" | "failed" | "running";

export interface GamingBuild {
  id: string;
  project_id: string;
  branch: string;
  build_number: string;
  game_version: string | null;
  engine_version: string;
  status: GamingBuildStatus;
  fps_avg: number | null;
  crashes: number | null;
  draw_calls: number | null;
  commit_sha: string | null;
  notes: string;
  created_at: string;
}

export interface GamingAsset {
  id: string;
  project_id: string;
  category: string;
  name: string;
  asset_type: string;
  file_path: string;
  size_bytes: number;
  modified_at: string | null;
  synced_at: string;
}

export interface GamingCommunityStats {
  steam_configured: boolean;
  steam_concurrent_players: number | null;
  discord_configured: boolean;
  discord_member_count: number | null;
}

export type RoboBuildStage = "Prototype" | "V2" | "V3" | "Certification" | "Production";

export interface RoboBuild {
  id: string;
  project_id: string;
  branch: string;
  stage: RoboBuildStage;
  version: string | null;
  pcb_revision: string | null;
  firmware_version: string | null;
  tests_passed_pct: number | null;
  open_issues: number | null;
  notes: string;
  created_at: string;
}

export type RoboLabTestStatus = "pass" | "fail" | "in_progress";

export interface RoboLabTest {
  id: string;
  project_id: string;
  category: string;
  name: string;
  status: RoboLabTestStatus;
  measured_value: string | null;
  notes: string;
  created_at: string;
}

export interface RoboTelemetry {
  id: string;
  project_id: string;
  power_w: number | null;
  temperature_c: number | null;
  cpu_pct: number | null;
  battery_pct: number | null;
  charge_cycles: number | null;
  autonomy_hours: number | null;
  created_at: string;
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
  agentId?: string;
  responseId?: string;
  userMessage?: string;
  issueCreated?: boolean;
  issueNumber?: number;
  issueUrl?: string;
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
