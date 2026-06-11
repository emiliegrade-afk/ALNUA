import { useWebSocket } from '@/hooks/useWebSocket'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function StatusBar() {
  const { isConnected: wsPipeline } = useWebSocket('/ws/pipeline')
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.get<{ status: string }>('/health').then((r) => r.data),
    refetchInterval: 60000,
    retry: 1,
  })

  const apiOk = health?.status === 'ok'

  return (
    <footer className="h-7 border-t border-alnua-border bg-alnua-surface flex items-center px-4 gap-4 text-xs text-alnua-muted shrink-0">
      <span className="flex items-center gap-1.5">
        <span className={`w-1.5 h-1.5 rounded-full ${apiOk ? 'bg-green-400' : 'bg-red-400'}`} />
        API {apiOk ? 'connectée' : 'hors ligne'}
      </span>
      <span className="flex items-center gap-1.5">
        <span className={`w-1.5 h-1.5 rounded-full ${wsPipeline ? 'bg-green-400' : 'bg-yellow-400'}`} />
        Pipeline WS {wsPipeline ? 'live' : 'reconnexion…'}
      </span>
      <span className="ml-auto font-mono">
        {new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
      </span>
    </footer>
  )
}
