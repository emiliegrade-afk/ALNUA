import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { DailyBrief } from '@/types'

export function BriefCard() {
  const { data: brief, isLoading } = useQuery({
    queryKey: ['brief', 'today'],
    queryFn: () => api.get<DailyBrief>('/brief/today').then((r) => r.data),
    staleTime: 1000 * 60 * 30,
  })

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-5 backdrop-blur-sm">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-lg">📋</span>
        <h2 className="font-semibold text-white font-heading">Brief du jour</h2>
        <span className="ml-auto text-xs text-gray-500">
          {new Date().toLocaleDateString('fr-FR', {
            weekday: 'long',
            day: 'numeric',
            month: 'long',
          })}
        </span>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-4 bg-gray-700 rounded animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Projets actifs</p>
            <div className="space-y-1">
              {brief?.projects?.length ? (
                brief.projects.map((p) => (
                  <div key={p.name} className="flex items-center gap-2">
                    <div
                      className={`w-2 h-2 rounded-full ${
                        p.branch === 'app'
                          ? 'bg-green-400'
                          : p.branch === 'gaming'
                            ? 'bg-amber-400'
                            : 'bg-blue-400'
                      }`}
                    />
                    <span className="text-sm text-gray-200">{p.name}</span>
                    <span className="ml-auto text-xs text-gray-500">{p.status}</span>
                  </div>
                ))
              ) : (
                <p className="text-sm text-gray-500">Aucun projet actif</p>
              )}
            </div>
          </div>

          {brief?.urgent && brief.urgent.length > 0 && (
            <div>
              <p className="text-xs text-red-400 uppercase tracking-wider mb-1">⚠️ Urgent</p>
              {brief.urgent.map((u, i) => (
                <p key={i} className="text-sm text-red-300">
                  {u}
                </p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
