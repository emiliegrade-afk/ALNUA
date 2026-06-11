import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useWebSocket } from '@/hooks/useWebSocket'
import { cn } from '@/components/ui/utils'

type COOState = 'idle' | 'thinking' | 'speaking' | 'error'

interface COOAvatarProps {
  onClick: () => void
}

export function COOAvatar({ onClick }: COOAvatarProps) {
  const [state, setCOOState] = useState<COOState>('idle')
  const { lastMessage } = useWebSocket('/ws/coo')

  useEffect(() => {
    if (lastMessage?.type === 'thinking') setCOOState('thinking')
    else if (lastMessage?.type === 'speaking') setCOOState('speaking')
    else if (lastMessage?.type === 'error') setCOOState('error')
    else if (lastMessage?.type === 'response') setCOOState('speaking')
    else setCOOState('idle')
  }, [lastMessage])

  const stateLabel =
    state === 'idle'
      ? 'Prêt'
      : state === 'thinking'
        ? 'Analyse...'
        : state === 'speaking'
          ? 'Répond...'
          : 'Erreur'

  return (
    <motion.div
      className="fixed bottom-6 right-6 z-50 cursor-pointer group"
      onClick={onClick}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
    >
      <motion.div
        className="absolute inset-0 rounded-full bg-violet-500"
        animate={{
          opacity: state === 'idle' ? [0.2, 0.4, 0.2] : [0.4, 0.7, 0.4],
          scale: state === 'thinking' ? [1, 1.2, 1] : [1, 1.05, 1],
        }}
        transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
        style={{ filter: 'blur(12px)' }}
      />

      <div className="relative w-16 h-16 rounded-full bg-gradient-to-br from-violet-600 to-indigo-800 border-2 border-violet-400 flex items-center justify-center shadow-accent-glow">
        {state === 'idle' && <span className="text-2xl">🤖</span>}
        {state === 'thinking' && (
          <motion.div
            className="w-6 h-6 border-2 border-white border-t-transparent rounded-full"
            animate={{ rotate: 360 }}
            transition={{ duration: 0.8, repeat: Infinity, ease: 'linear' }}
          />
        )}
        {state === 'speaking' && (
          <div className="flex gap-1 items-center">
            {[0, 1, 2, 3].map((i) => (
              <motion.div
                key={i}
                className="w-1 bg-white rounded-full"
                animate={{ height: ['8px', '20px', '8px'] }}
                transition={{
                  duration: 0.6,
                  repeat: Infinity,
                  delay: i * 0.1,
                  ease: 'easeInOut',
                }}
              />
            ))}
          </div>
        )}
        {state === 'error' && <span className="text-2xl">⚠️</span>}

        <div
          className={cn(
            'absolute -top-1 -right-1 w-4 h-4 rounded-full border-2 border-gray-900',
            state === 'idle' && 'bg-green-400',
            state === 'thinking' && 'bg-yellow-400',
            state === 'speaking' && 'bg-blue-400',
            state === 'error' && 'bg-red-400',
          )}
        />
      </div>

      <div className="absolute bottom-full right-0 mb-2 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 whitespace-nowrap transition-opacity pointer-events-none">
        COO Agent — {stateLabel}
      </div>
    </motion.div>
  )
}
