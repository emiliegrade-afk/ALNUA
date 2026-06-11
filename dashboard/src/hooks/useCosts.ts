import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { WeekCosts } from '@/types'

export function useCosts() {
  return useQuery({
    queryKey: ['costs', 'week'],
    queryFn: () => api.get<WeekCosts>('/costs/week').then((r) => r.data),
    staleTime: 1000 * 60 * 15,
  })
}
