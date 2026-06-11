import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { EveStatus } from '@/types'

export function RoboBranch() {
  const { data: eveStatus } = useQuery({
    queryKey: ['eve', 'status'],
    queryFn: () => api.get<EveStatus>('/eve/status').then((r) => r.data),
    refetchInterval: 30000,
    retry: 1,
  })

  const isOnline = eveStatus?.connected === true

  return (
    <div className="bg-gray-800/50 border border-blue-800/50 rounded-xl p-4 hover:border-blue-600/50 transition-colors">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-3 h-3 rounded-full bg-blue-400" />
        <h3 className="font-semibold text-blue-400 font-heading">Pôle Robotique</h3>
      </div>

      <div className="bg-gray-900/50 rounded-lg p-3 mb-3">
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${isOnline ? 'bg-green-400 animate-pulse' : 'bg-gray-500'}`}
          />
          <span className="text-sm font-medium text-gray-200">Eve Robot</span>
          <span className={`ml-auto text-xs ${isOnline ? 'text-green-400' : 'text-gray-500'}`}>
            {isOnline ? '🟢 En ligne' : '⚫ Hors ligne'}
          </span>
        </div>
        {isOnline && eveStatus?.battery != null && (
          <div className="mt-2 flex items-center gap-2">
            <span className="text-xs text-gray-400">Batterie</span>
            <div className="flex-1 h-1 bg-gray-700 rounded-full">
              <div
                className={`h-full rounded-full ${
                  eveStatus.battery > 50
                    ? 'bg-green-500'
                    : eveStatus.battery > 20
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                }`}
                style={{ width: `${eveStatus.battery}%` }}
              />
            </div>
            <span className="text-xs text-gray-400">{eveStatus.battery}%</span>
          </div>
        )}
      </div>

      <div className="space-y-1">
        {[
          { name: 'Eve Robot', status: 'Prototype', progress: 25 },
          { name: 'Looking Glass', status: 'À démarrer', progress: 0 },
        ].map((project) => (
          <div key={project.name}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm text-gray-200">{project.name}</span>
              <span className="text-xs text-gray-400">{project.status}</span>
            </div>
            <div className="h-1.5 bg-gray-700 rounded-full">
              <div
                className="h-full bg-blue-500 rounded-full"
                style={{ width: `${project.progress}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      <div className="mt-3 flex gap-2 flex-wrap">
        {['Hardware', 'Embedded'].map((agent) => (
          <span
            key={agent}
            className="text-xs bg-blue-900/50 text-blue-400 px-2 py-0.5 rounded-full"
          >
            {agent}
          </span>
        ))}
      </div>
    </div>
  )
}
