import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { Agent, AgentLog, AgentStatus, Branch } from '@/types'

const KNOWN_AGENTS: Omit<Agent, 'status' | 'lastAction'>[] = [
  { id: 'coo', name: 'COO', displayName: 'COO', branch: 'all' },
  { id: 'dev_app', name: 'DevApp', displayName: 'Dev App', branch: 'app' },
  { id: 'pm', name: 'PM', displayName: 'PM', branch: 'app' },
  { id: 'game_director', name: 'GameDirector', displayName: 'Game Director', branch: 'gaming' },
  { id: 'dev_gaming', name: 'DevGaming', displayName: 'Dev Gaming', branch: 'gaming' },
  { id: 'hardware', name: 'Hardware', displayName: 'Hardware', branch: 'robotics' },
  { id: 'embedded', name: 'EmbeddedDev', displayName: 'Embedded Dev', branch: 'robotics' },
  { id: 'marketing', name: 'Marketing', displayName: 'Marketing', branch: 'all' },
]

function deriveStatus(log: AgentLog | undefined): AgentStatus {
  if (!log) return 'idle'
  if (log.status === 'error') return 'error'
  if (log.status === 'pending' || log.status === 'in_progress') return 'thinking'
  const age = Date.now() - new Date(log.created_at).getTime()
  if (age < 5 * 60 * 1000) return 'active'
  return 'idle'
}

function matchAgent(logAgent: string): string | null {
  const normalized = logAgent.toLowerCase().replace(/[_\s-]/g, '')
  for (const agent of KNOWN_AGENTS) {
    const id = agent.id.replace(/_/g, '')
    const name = agent.name.toLowerCase()
    if (normalized.includes(id) || normalized.includes(name.toLowerCase())) {
      return agent.id
    }
  }
  return null
}

export function useAgents() {
  const { data: logs, isLoading, error } = useQuery({
    queryKey: ['agents', 'logs'],
    queryFn: () => api.get<AgentLog[]>('/agents/logs?limit=50').then((r) => r.data),
    refetchInterval: 30000,
  })

  const latestByAgent = new Map<string, AgentLog>()
  for (const log of logs ?? []) {
    const id = matchAgent(log.agent)
    if (!id) continue
    const existing = latestByAgent.get(id)
    if (!existing || new Date(log.created_at) > new Date(existing.created_at)) {
      latestByAgent.set(id, log)
    }
  }

  const agents: Agent[] = KNOWN_AGENTS.map((base) => {
    const log = latestByAgent.get(base.id)
    return {
      ...base,
      status: deriveStatus(log),
      lastAction: log?.output_summary?.slice(0, 80),
    }
  })

  const byBranch = (branch: Branch) => agents.filter((a) => a.branch === branch || a.branch === 'all')

  return { agents, byBranch, isLoading, error }
}
