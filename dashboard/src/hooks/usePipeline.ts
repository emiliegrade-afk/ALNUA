import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { GitHubIssue, GitHubPR } from '@/types'

export function usePipeline() {
  const issues = useQuery({
    queryKey: ['issues', 'ready'],
    queryFn: () => api.get<GitHubIssue[]>('/pipeline/issues').then((r) => r.data),
    refetchInterval: 30000,
  })

  const prs = useQuery({
    queryKey: ['prs', 'open'],
    queryFn: () => api.get<GitHubPR[]>('/github/prs').then((r) => r.data),
    refetchInterval: 60000,
  })

  const runIssue = async (issueNumber: number) => {
    await api.post(`/pipeline/run/${issueNumber}`)
  }

  return {
    issues: issues.data ?? [],
    prs: prs.data ?? [],
    isLoadingIssues: issues.isLoading,
    isLoadingPrs: prs.isLoading,
    runIssue,
  }
}
