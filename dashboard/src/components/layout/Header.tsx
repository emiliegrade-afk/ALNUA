import { Bell, User } from 'lucide-react'

export function Header() {
  return (
    <header className="h-14 border-b border-alnua-border bg-alnua-surface/80 backdrop-blur-sm flex items-center px-6 gap-4 shrink-0">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-600 to-indigo-700 flex items-center justify-center font-heading font-bold text-sm">
          A
        </div>
        <span className="font-heading font-semibold text-lg tracking-tight">ALNUA Hub</span>
      </div>

      <div className="ml-auto flex items-center gap-3">
        <button
          type="button"
          className="p-2 rounded-lg text-alnua-muted hover:text-alnua-text hover:bg-alnua-surface-2 transition"
          aria-label="Notifications"
        >
          <Bell className="w-4 h-4" />
        </button>
        <div className="flex items-center gap-2 pl-3 border-l border-alnua-border">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-pink-500 flex items-center justify-center">
            <User className="w-4 h-4" />
          </div>
          <div className="hidden sm:block">
            <p className="text-sm font-medium">Emilie</p>
            <p className="text-xs text-alnua-muted">CEO · ALNUA</p>
          </div>
        </div>
      </div>
    </header>
  )
}
