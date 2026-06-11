import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { BranchData } from '@/types'

const FALLBACK_PROJECTS = [
  { name: 'Naïa App', status: 'MVP quasi fini', progress: 85 },
  { name: "Eve Journey's", status: 'En cours', progress: 40 },
  { name: 'naia-embodied', status: 'Déployé ✓', progress: 100 },
]

export function AppBranch() {
  const { data } = useQuery({
    queryKey: ['branch', 'app'],
    queryFn: () => api.get<BranchData>('/branches/app').then((r) => r.data),
    retry: 1,
  })

  const projects = data?.projects?.length ? data.projects : FALLBACK_PROJECTS

  return (
    <div className="bg-gray-800/50 border border-green-800/50 rounded-xl p-4 hover:border-green-600/50 transition-colors">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-3 h-3 rounded-full bg-green-400" />
        <h3 className="font-semibold text-green-400 font-heading">Pôle App</h3>
      </div>

      <div className="space-y-2">
        {projects.map((project) => (
          <div key={project.name}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm text-gray-200">{project.name}</span>
              <span className="text-xs text-gray-400">{project.status}</span>
            </div>
            <div className="h-1.5 bg-gray-700 rounded-full">
              <div
                className="h-full bg-green-500 rounded-full transition-all"
                style={{ width: `${project.progress}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      <div className="mt-3 flex gap-2 flex-wrap">
        {(data?.agents ?? ['DevApp', 'UX']).map((agent) => (
          <span
            key={agent}
            className="text-xs bg-green-900/50 text-green-400 px-2 py-0.5 rounded-full"
          >
            {agent}
          </span>
        ))}
      </div>
    </div>
  )
}
