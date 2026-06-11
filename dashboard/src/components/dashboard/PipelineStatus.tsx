import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { api } from '@/lib/api'
import { useWebSocket } from '@/hooks/useWebSocket'
import type { GitHubIssue, GitHubPR } from '@/types'

export function PipelineStatus() {
  const [runningTask, setRunningTask] = useState<string | null>(null)
  const { lastMessage: pipelineUpdate } = useWebSocket('/ws/pipeline')

  const { data: issues } = useQuery({
    queryKey: ['issues', 'ready'],
    queryFn: () => api.get<GitHubIssue[]>('/pipeline/issues').then((r) => r.data),
    refetchInterval: 30000,
  })

  const { data: prs } = useQuery({
    queryKey: ['prs', 'open'],
    queryFn: () => api.get<GitHubPR[]>('/github/prs').then((r) => r.data),
    refetchInterval: 60000,
  })

  const handleRunIssue = async (issueNumber: number) => {
    setRunningTask(`#${issueNumber}`)
    try {
      await api.post(`/pipeline/run/${issueNumber}`)
    } finally {
      setTimeout(() => setRunningTask(null), 5000)
    }
  }

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-5 backdrop-blur-sm">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-lg">⚙️</span>
        <h2 className="font-semibold text-white font-heading">Pipeline Codage</h2>
        {runningTask && (
          <span className="ml-auto text-xs text-yellow-400 animate-pulse">
            🔧 {runningTask} en cours...
          </span>
        )}
      </div>

      <div className="mb-4">
        <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">
          Issues prêtes ({issues?.length || 0})
        </p>
        {!issues?.length ? (
          <p className="text-sm text-gray-500">Aucune issue en attente</p>
        ) : (
          <div className="space-y-2">
            {issues.slice(0, 3).map((issue) => (
              <div
                key={issue.number}
                className="flex items-center gap-2 bg-gray-700/50 rounded-lg px-3 py-2"
              >
                <span className="text-xs text-gray-400">#{issue.number}</span>
                <span className="text-sm text-gray-200 flex-1 truncate">{issue.title}</span>
                <button
                  type="button"
                  onClick={() => handleRunIssue(issue.number)}
                  className="text-xs bg-violet-600 hover:bg-violet-500 text-white px-2 py-0.5 rounded transition"
                >
                  Lancer
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div>
        <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">
          PRs ouvertes ({prs?.length || 0})
        </p>
        {prs?.slice(0, 2).map((pr) => (
          <div key={pr.number} className="flex items-center gap-2 mb-2">
            <div className={`w-2 h-2 rounded-full ${pr.auto ? 'bg-violet-400' : 'bg-gray-400'}`} />
            <span className="text-sm text-gray-200 flex-1 truncate">PR #{pr.number}</span>
            <a
              href={pr.url}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-violet-400 hover:text-violet-300"
            >
              Voir →
            </a>
          </div>
        ))}
      </div>

      {pipelineUpdate?.message && (
        <div className="mt-3 bg-gray-900 rounded-lg px-3 py-2">
          <p className="text-xs font-mono text-green-400">{pipelineUpdate.message}</p>
        </div>
      )}
    </div>
  )
}
