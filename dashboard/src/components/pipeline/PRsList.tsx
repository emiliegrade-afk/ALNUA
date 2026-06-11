import { usePipeline } from '@/hooks/usePipeline'
import { ExternalLink } from 'lucide-react'

export function PRsList() {
  const { prs, isLoadingPrs } = usePipeline()

  if (isLoadingPrs) {
    return <div className="h-32 bg-alnua-surface-2 rounded-xl animate-pulse" />
  }

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-5">
      <h2 className="font-semibold text-white font-heading mb-4">
        Pull Requests ouvertes ({prs.length})
      </h2>
      {!prs.length ? (
        <p className="text-sm text-gray-500">Aucune PR ouverte</p>
      ) : (
        <div className="space-y-2">
          {prs.map((pr) => (
            <div
              key={pr.number}
              className="flex items-center gap-3 bg-gray-700/50 rounded-lg px-4 py-3"
            >
              <div className={`w-2 h-2 rounded-full ${pr.auto ? 'bg-violet-400' : 'bg-gray-400'}`} />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-200 truncate">
                  PR #{pr.number} — {pr.title}
                </p>
                {pr.auto && (
                  <span className="text-xs text-violet-400">Agent automatique</span>
                )}
              </div>
              <a
                href={pr.url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1 text-xs text-violet-400 hover:text-violet-300"
              >
                Voir <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
