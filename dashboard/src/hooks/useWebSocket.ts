import { useState, useEffect, useRef, useMemo } from 'react'
import type { WSMessage } from '@/types'

export function useWebSocket(path: string) {
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  const WS_URL = useMemo(() => API_URL.replace(/^http/, 'ws'), [API_URL])

  useEffect(() => {
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null
    let closed = false

    const connect = () => {
      if (closed) return
      try {
        const ws = new WebSocket(`${WS_URL}${path}`)
        wsRef.current = ws

        ws.onopen = () => setIsConnected(true)
        ws.onclose = () => {
          setIsConnected(false)
          if (!closed) {
            reconnectTimer = setTimeout(connect, 3000)
          }
        }
        ws.onerror = () => ws.close()
        ws.onmessage = (event) => {
          try {
            setLastMessage(JSON.parse(event.data) as WSMessage)
          } catch {
            setLastMessage({ type: 'raw', message: event.data })
          }
        }
      } catch {
        if (!closed) {
          reconnectTimer = setTimeout(connect, 3000)
        }
      }
    }

    connect()

    return () => {
      closed = true
      if (reconnectTimer) clearTimeout(reconnectTimer)
      wsRef.current?.close()
    }
  }, [path, WS_URL])

  const send = (data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }

  return { lastMessage, isConnected, send }
}
