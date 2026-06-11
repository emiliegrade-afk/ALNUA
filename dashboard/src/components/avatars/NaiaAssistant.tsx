import { useState } from 'react'
import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useNavigate } from 'react-router-dom'

interface NaiaMessage {
  text: string
  type: 'info' | 'suggestion' | 'alert'
}

export function NaiaAssistant() {
  const [isExpanded, setIsExpanded] = useState(false)
  const navigate = useNavigate()

  const { data: issues } = useQuery({
    queryKey: ['issues', 'ready'],
    queryFn: () => api.get<unknown[]>('/pipeline/issues').then((r) => r.data),
    refetchInterval: 60000,
    retry: 1,
  })

  const issueCount = issues?.length ?? 0
  const message: NaiaMessage = {
    text:
      issueCount > 0
        ? `Bonjour Emilie ! ${issueCount} issue${issueCount > 1 ? 's' : ''} GitHub ${issueCount > 1 ? 'sont' : 'est'} prête${issueCount > 1 ? 's' : ''} à être traitée${issueCount > 1 ? 's' : ''}.`
        : 'Bonjour Emilie ! Tout est calme côté pipeline aujourd\'hui.',
    type: issueCount > 0 ? 'suggestion' : 'info',
  }

  return (
    <div className="p-4 border-b border-gray-700">
      <div
        className="flex items-center gap-3 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
        onKeyDown={(e) => e.key === 'Enter' && setIsExpanded(!isExpanded)}
        role="button"
        tabIndex={0}
      >
        <div className="relative">
          <motion.div
            className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 to-pink-500 flex items-center justify-center text-lg shadow-lg"
            animate={{ scale: [1, 1.02, 1] }}
            transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
          >
            ✨
          </motion.div>
          <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-400 rounded-full border border-gray-900" />
        </div>

        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-white">Naïa</p>
          <p className="text-xs text-gray-400 truncate">{message.text}</p>
        </div>
      </div>

      {isExpanded && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="mt-3 bg-gray-800 rounded-lg p-3"
        >
          <p className="text-sm text-gray-200">{message.text}</p>
          {issueCount > 0 && (
            <div className="flex gap-2 mt-2">
              <button
                type="button"
                onClick={() => navigate('/pipeline')}
                className="text-xs bg-violet-600 hover:bg-violet-500 text-white px-3 py-1 rounded-full transition"
              >
                Traiter
              </button>
              <button
                type="button"
                onClick={() => setIsExpanded(false)}
                className="text-xs bg-gray-700 hover:bg-gray-600 text-white px-3 py-1 rounded-full transition"
              >
                Plus tard
              </button>
            </div>
          )}
          {message.type === 'info' && (
            <div className="flex gap-1 mt-2">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
          )}
        </motion.div>
      )}
    </div>
  )
}
