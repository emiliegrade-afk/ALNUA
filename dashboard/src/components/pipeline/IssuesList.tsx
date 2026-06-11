import { usePipeline } from '@/hooks/usePipeline'
import { useState } from 'react'

export function IssuesList() {
  const { issues, isLoadingIssues, runIssue } = usePipeline()
  const [running, setRunning] = useState<number | null>(null)

  const handleRun = async (num: number) => {
    setRunning(num)
    try {
      await runIssue(num)
    } finally {
      setTimeout(() => setRunning(null), 3000)
    }
  }

  if (isLoadingIssues) {
    return <div className="h-32 bg-alnua-surface-2 rounded-xl animate-pulse" />
  }

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-5">
      <h2 className="font-semibold text-white font-heading mb-4">
        Issues agent-ready ({issues.length})
      </h2>
      {!issues.length ? (
        <p className="text-sm text-gray-500">Aucune issue en attente</p>
      ) : (
        <div className="space-y-2">
          {issues.map((issue) => (
            <div
              key={issue.number}
              className="flex items-center gap-3 bg-gray-700/50 rounded-lg px-4 py-3"
            >
              <span className="text-xs text-gray-400 font-mono">#{issue.number}</span>
              <span className="text-sm text-gray-200 flex-1">{issue.title}</span>
              {issue.html_url && (
                <a
                  href={issue.html_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-violet-400 hover:text-violet-300"
                >
                  GitHub
                </a>
              )}
              <button
                type="button"
                onClick={() => handleRun(issue.number)}
                disabled={running === issue.number}
                className="text-xs bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white px-3 py-1 rounded transition"
              >
                {running === issue.number ? 'Lancement…' : 'Lancer'}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
