export type Branch = 'app' | 'gaming' | 'robotics'

export type AgentStatus = 'idle' | 'active' | 'thinking' | 'error'

export interface Agent {
  id: string
  name: string
  displayName: string
  branch: Branch | 'all'
  status: AgentStatus
  lastAction?: string
}

export interface BriefProject {
  name: string
  branch: Branch
  status: string
}

export interface DailyBrief {
  date: string
  projects: BriefProject[]
  urgent: string[]
  summary?: string
}

export interface GitHubIssue {
  number: number
  title: string
  labels?: { name: string }[]
  html_url?: string
}

export interface GitHubPR {
  number: number
  title: string
  url: string
  auto?: boolean
}

export interface EveStatus {
  connected: boolean
  battery: number | null
  raw?: string
}

export interface WeekCosts {
  total_usd: number
  by_day: Record<string, number | string>[]
}

export interface WSMessage {
  type: string
  message: string
  data?: unknown
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export interface AgentLog {
  id: string
  agent: string
  action: string
  input_summary: string
  output_summary: string
  status: string
  created_at: string
}

export interface BranchData {
  projects: { name: string; status: string; progress: number }[]
  agents: string[]
}
