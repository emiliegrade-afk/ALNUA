import { NavLink } from 'react-router-dom'
import { LayoutDashboard, GitBranch, Bot, Cpu, Gamepad2, Smartphone } from 'lucide-react'
import { NaiaAssistant } from '@/components/avatars/NaiaAssistant'
import { useAgents } from '@/hooks/useAgents'
import { cn } from '@/components/ui/utils'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/agents', label: 'Agents', icon: Bot },
  { to: '/pipeline', label: 'Pipeline', icon: GitBranch },
  { to: '/branch/app', label: 'Pôle App', icon: Smartphone, color: 'text-alnua-app' },
  { to: '/branch/gaming', label: 'Pôle Gaming', icon: Gamepad2, color: 'text-alnua-gaming' },
  { to: '/branch/robo', label: 'Pôle Robotique', icon: Cpu, color: 'text-alnua-robo' },
]

export function Sidebar() {
  const { agents } = useAgents()
  const activeCount = agents.filter((a) => a.status === 'active' || a.status === 'thinking').length

  return (
    <aside className="w-64 border-r border-alnua-border bg-alnua-surface flex flex-col shrink-0">
      <NaiaAssistant />

      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {navItems.map(({ to, label, icon: Icon, color }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition',
                isActive
                  ? 'bg-violet-600/20 text-violet-300 border border-violet-600/30'
                  : 'text-alnua-muted hover:text-alnua-text hover:bg-alnua-surface-2',
              )
            }
          >
            <Icon className={cn('w-4 h-4', color)} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-alnua-border">
        <p className="text-xs text-alnua-muted uppercase tracking-wider mb-2">Agents</p>
        <div className="flex items-center gap-2">
          <div className="flex -space-x-1">
            {agents.slice(0, 5).map((agent) => (
              <div
                key={agent.id}
                title={agent.displayName}
                className={cn(
                  'w-6 h-6 rounded-full border-2 border-alnua-surface flex items-center justify-center text-[10px]',
                  agent.status === 'active' || agent.status === 'thinking'
                    ? 'bg-violet-600'
                    : 'bg-alnua-surface-2',
                )}
              >
                {agent.name.charAt(0)}
              </div>
            ))}
          </div>
          <span className="text-xs text-alnua-muted">
            {activeCount} actif{activeCount !== 1 ? 's' : ''}
          </span>
        </div>
      </div>
    </aside>
  )
}
