import { useState, useRef, useEffect } from 'react'
import { Send } from 'lucide-react'
import { useChatStore } from '@/stores/chatStore'
import { useWebSocket } from '@/hooks/useWebSocket'
import { api } from '@/lib/api'

interface AgentChatProps {
  agentId: string
  agentName: string
  useWebSocket?: boolean
}

export function AgentChat({ agentId, agentName, useWebSocket: wsEnabled = false }: AgentChatProps) {
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { messages, addMessage } = useChatStore()
  const agentMessages = messages[agentId] ?? []
  const { send: wsSend, lastMessage } = useWebSocket('/ws/coo')

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [agentMessages])

  useEffect(() => {
    if (wsEnabled && lastMessage?.type === 'response' && lastMessage.message) {
      addMessage(agentId, { role: 'assistant', content: lastMessage.message })
      setSending(false)
    }
  }, [lastMessage, wsEnabled, agentId, addMessage])

  const handleSend = async () => {
    const text = input.trim()
    if (!text || sending) return

    setInput('')
    setSending(true)
    addMessage(agentId, { role: 'user', content: text })

    try {
      if (wsEnabled && agentId === 'coo') {
        wsSend({ message: text })
      } else {
        const { data } = await api.post<{ response: string }>('/agents/coo/instruction', {
          instruction: text,
        })
        addMessage(agentId, { role: 'assistant', content: data.response })
        setSending(false)
      }
    } catch {
      addMessage(agentId, {
        role: 'assistant',
        content: 'Erreur de connexion à l\'API. Vérifie que le serveur FastAPI tourne.',
      })
      setSending(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-[200px] max-h-[400px]">
        {agentMessages.length === 0 && (
          <p className="text-sm text-alnua-muted text-center py-8">
            Envoie un message à {agentName}…
          </p>
        )}
        {agentMessages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-xl px-3 py-2 text-sm ${
                msg.role === 'user'
                  ? 'bg-violet-600 text-white'
                  : 'bg-alnua-surface-2 text-alnua-text'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {sending && (
          <div className="flex gap-1 px-2">
            <span className="typing-dot" />
            <span className="typing-dot" />
            <span className="typing-dot" />
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-3 border-t border-alnua-border flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder={`Message à ${agentName}…`}
          className="flex-1 bg-alnua-surface-2 border border-alnua-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-violet-500"
        />
        <button
          type="button"
          onClick={handleSend}
          disabled={sending || !input.trim()}
          className="p-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 rounded-lg transition"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
