import { X } from 'lucide-react'
import { AgentChat } from './AgentChat'
import { useAgents } from '@/hooks/useAgents'

interface AgentPanelProps {
  agentId: string
  onClose: () => void
}

export function AgentPanel({ agentId, onClose }: AgentPanelProps) {
  const { agents } = useAgents()
  const agent = agents.find((a) => a.id === agentId)
  const displayName = agent?.displayName ?? 'Agent'

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-96 bg-alnua-surface border-l border-alnua-border shadow-2xl z-40 flex flex-col">
      <div className="flex items-center justify-between p-4 border-b border-alnua-border">
        <h2 className="font-heading font-semibold">{displayName}</h2>
        <button
          type="button"
          onClick={onClose}
          className="p-1.5 rounded-lg hover:bg-alnua-surface-2 transition"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
      <AgentChat agentId={agentId} agentName={displayName} useWebSocket={agentId === 'coo'} />
    </div>
  )
}
