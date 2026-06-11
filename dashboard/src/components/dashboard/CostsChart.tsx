import { useQuery } from '@tanstack/react-query'
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { api } from '@/lib/api'
import type { WeekCosts } from '@/types'

const AGENT_COLORS: Record<string, string> = {
  COO: '#6366F1',
  DevApp: '#10B981',
  GameDirector: '#F59E0B',
  DevGaming: '#F97316',
  Hardware: '#3B82F6',
  EmbeddedDev: '#06B6D4',
  Marketing: '#EC4899',
}

export function CostsChart() {
  const { data: weekCosts } = useQuery({
    queryKey: ['costs', 'week'],
    queryFn: () => api.get<WeekCosts>('/costs/week').then((r) => r.data),
    staleTime: 1000 * 60 * 15,
  })

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-5 backdrop-blur-sm">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-lg">💰</span>
        <h2 className="font-semibold text-white font-heading">Coûts LLM — 7 jours</h2>
        <span className="ml-auto text-sm text-gray-400">
          Total :{' '}
          <span className="text-white font-medium">
            ${weekCosts?.total_usd?.toFixed(3) || '0.000'}
          </span>
        </span>
      </div>

      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={weekCosts?.by_day || []}>
          <XAxis dataKey="date" tick={{ fill: '#9CA3AF', fontSize: 11 }} />
          <YAxis tick={{ fill: '#9CA3AF', fontSize: 11 }} tickFormatter={(v) => `$${v}`} />
          <Tooltip
            contentStyle={{
              background: '#1F2937',
              border: '1px solid #374151',
              borderRadius: '8px',
            }}
            labelStyle={{ color: '#F9FAFB' }}
            formatter={(value: number, name: string) => [`$${value.toFixed(4)}`, name]}
          />
          <Legend wrapperStyle={{ fontSize: '12px' }} />
          {Object.entries(AGENT_COLORS).map(([agent, color]) => (
            <Bar key={agent} dataKey={agent} stackId="a" fill={color} radius={[2, 2, 0, 0]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
