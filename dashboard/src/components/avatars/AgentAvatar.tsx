import { motion } from 'framer-motion'
import type { AgentStatus } from '@/types'
import { cn } from '@/components/ui/utils'

interface AgentAvatarProps {
  name: string
  emoji?: string
  status: AgentStatus
  size?: 'sm' | 'md' | 'lg'
  branchColor?: string
  onClick?: () => void
}

const sizeClasses = {
  sm: 'w-8 h-8 text-sm',
  md: 'w-10 h-10 text-base',
  lg: 'w-14 h-14 text-xl',
}

const statusColors: Record<AgentStatus, string> = {
  idle: 'bg-gray-500',
  active: 'bg-green-400',
  thinking: 'bg-yellow-400 animate-pulse',
  error: 'bg-red-400',
}

export function AgentAvatar({
  name,
  emoji,
  status,
  size = 'md',
  branchColor = 'from-violet-600 to-indigo-700',
  onClick,
}: AgentAvatarProps) {
  const initial = name.charAt(0).toUpperCase()

  return (
    <motion.button
      type="button"
      onClick={onClick}
      className={cn('relative rounded-full shrink-0', sizeClasses[size], onClick && 'cursor-pointer')}
      whileHover={onClick ? { scale: 1.05 } : undefined}
      whileTap={onClick ? { scale: 0.95 } : undefined}
      title={name}
    >
      <div
        className={cn(
          'w-full h-full rounded-full bg-gradient-to-br flex items-center justify-center font-semibold border border-white/10',
          branchColor,
          (status === 'active' || status === 'thinking') && 'agent-card-active',
        )}
      >
        {emoji ?? initial}
      </div>
      <span
        className={cn(
          'absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-alnua-surface',
          statusColors[status],
        )}
      />
    </motion.button>
  )
}
