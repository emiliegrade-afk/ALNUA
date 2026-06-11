import { useAgents } from '@/hooks/useAgents'
import { AgentAvatar } from '@/components/avatars/AgentAvatar'
import { cn } from '@/components/ui/utils'

interface AgentListProps {
  onSelect?: (agentId: string) => void
  selectedId?: string | null
}

const branchGradients: Record<string, string> = {
  all: 'from-violet-600 to-indigo-700',
  app: 'from-green-600 to-emerald-700',
  gaming: 'from-amber-500 to-orange-600',
  robotics: 'from-blue-600 to-cyan-700',
}

export function AgentList({ onSelect, selectedId }: AgentListProps) {
  const { agents, isLoading } = useAgents()

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-14 bg-alnua-surface-2 rounded-lg animate-pulse" />
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-1">
      {agents.map((agent) => (
        <button
          key={agent.id}
          type="button"
          onClick={() => onSelect?.(agent.id)}
          className={cn(
            'w-full flex items-center gap-3 p-3 rounded-lg transition text-left',
            selectedId === agent.id
              ? 'bg-violet-600/20 border border-violet-600/30'
              : 'hover:bg-alnua-surface-2',
            (agent.status === 'active' || agent.status === 'thinking') && 'agent-card-active',
          )}
        >
          <AgentAvatar
            name={agent.displayName}
            status={agent.status}
            size="sm"
            branchColor={branchGradients[agent.branch] ?? branchGradients.all}
          />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium">{agent.displayName}</p>
            {agent.lastAction && (
              <p className="text-xs text-alnua-muted truncate">{agent.lastAction}</p>
            )}
          </div>
          <span
            className={cn(
              'text-xs px-2 py-0.5 rounded-full',
              agent.status === 'active' && 'bg-green-900/50 text-green-400',
              agent.status === 'thinking' && 'bg-yellow-900/50 text-yellow-400',
              agent.status === 'idle' && 'bg-gray-800 text-gray-400',
              agent.status === 'error' && 'bg-red-900/50 text-red-400',
            )}
          >
            {agent.status}
          </span>
        </button>
      ))}
    </div>
  )
}
