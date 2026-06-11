export function GamingBranch() {
  return (
    <div className="bg-gray-800/50 border border-amber-800/50 rounded-xl p-4 hover:border-amber-600/50 transition-colors">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-3 h-3 rounded-full bg-amber-400" />
        <h3 className="font-semibold text-amber-400 font-heading">Pôle Gaming</h3>
      </div>

      <div className="space-y-2">
        {[
          { name: 'Wyrdheim Online', status: 'R&D', progress: 15 },
          { name: 'Naïa World', status: 'R&D', progress: 10 },
        ].map((project) => (
          <div key={project.name}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm text-gray-200">{project.name}</span>
              <span className="text-xs text-gray-400">{project.status}</span>
            </div>
            <div className="h-1.5 bg-gray-700 rounded-full">
              <div
                className="h-full bg-amber-500 rounded-full"
                style={{ width: `${project.progress}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      <div className="mt-3 flex gap-2 flex-wrap">
        {['Game Director', 'Dev Gaming', 'Art Director'].map((agent) => (
          <span
            key={agent}
            className="text-xs bg-amber-900/50 text-amber-400 px-2 py-0.5 rounded-full"
          >
            {agent}
          </span>
        ))}
      </div>
    </div>
  )
}
