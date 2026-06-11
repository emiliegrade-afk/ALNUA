import { useWebSocket } from '@/hooks/useWebSocket'
import { useState, useEffect, useRef } from 'react'

interface LogEntry {
  id: number
  time: string
  message: string
  type: string
}

export function PipelineLog() {
  const { lastMessage, isConnected } = useWebSocket('/ws/pipeline')
  const [logs, setLogs] = useState<LogEntry[]>([])
  const logIdRef = useRef(0)

  useEffect(() => {
    if (!lastMessage) return
    const entry: LogEntry = {
      id: ++logIdRef.current,
      time: new Date().toLocaleTimeString('fr-FR'),
      message: lastMessage.message || JSON.stringify(lastMessage),
      type: lastMessage.type,
    }
    setLogs((prev) => [entry, ...prev].slice(0, 50))
  }, [lastMessage])

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <h2 className="font-semibold text-white font-heading">Log temps réel</h2>
        <span
          className={`ml-auto text-xs ${isConnected ? 'text-green-400' : 'text-yellow-400'}`}
        >
          {isConnected ? '● Connecté' : '○ Reconnexion…'}
        </span>
      </div>
      <div className="bg-gray-900 rounded-lg p-3 h-64 overflow-y-auto font-mono text-xs space-y-1">
        {logs.length === 0 ? (
          <p className="text-gray-500">En attente d&apos;événements pipeline…</p>
        ) : (
          logs.map((log) => (
            <div key={log.id} className="flex gap-2">
              <span className="text-gray-500 shrink-0">{log.time}</span>
              <span
                className={
                  log.type === 'error'
                    ? 'text-red-400'
                    : log.type === 'heartbeat'
                      ? 'text-gray-500'
                      : 'text-green-400'
                }
              >
                [{log.type}] {log.message}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
