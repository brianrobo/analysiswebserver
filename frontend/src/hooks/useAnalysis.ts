import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { analysisApi } from '@/api/analysis.api'
import type { ShareRequest } from '@/api/types'

export const analysisKeys = {
  history: (limit?: number, offset?: number) =>
    ['analysis', 'history', { limit, offset }] as const,
  detail: (jobId: number) => ['analysis', 'detail', jobId] as const,
  result: (jobId: number) => ['analysis', 'result', jobId] as const,
  stats: ['analysis', 'stats'] as const,
  sharedWithMe: (limit?: number, offset?: number) =>
    ['analysis', 'sharedWithMe', { limit, offset }] as const,
}

export function useAnalysisHistory(limit = 20, offset = 0) {
  return useQuery({
    queryKey: analysisKeys.history(limit, offset),
    queryFn: () => analysisApi.getHistory(limit, offset),
  })
}

export function useAnalysisStatus(jobId: number, enabled = true) {
  return useQuery({
    queryKey: analysisKeys.detail(jobId),
    queryFn: () => analysisApi.getStatus(jobId),
    enabled,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === 'running' || status === 'pending') return 5000
      return false
    },
  })
}

export function useAnalysisResult(jobId: number, enabled = true) {
  return useQuery({
    queryKey: analysisKeys.result(jobId),
    queryFn: () => analysisApi.getResult(jobId),
    enabled,
    staleTime: 1000 * 60 * 60 * 24, // 24h
  })
}

export function useUploadAnalysis() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ file, jobName }: { file: File; jobName?: string }) =>
      analysisApi.uploadFile(file, jobName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analysis', 'history'] })
    },
  })
}

export function useFromPathAnalysis() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ path, jobName }: { path: string; jobName?: string }) =>
      analysisApi.fromPath(path, jobName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analysis', 'history'] })
    },
  })
}

export function useDeleteAnalysis() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (jobId: number) => analysisApi.deleteJob(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analysis', 'history'] })
    },
  })
}

export function useShareAnalysis() {
  return useMutation({
    mutationFn: ({ jobId, request }: { jobId: number; request: ShareRequest }) =>
      analysisApi.shareWithTeam(jobId, request),
  })
}

export function useSharedWithMe(limit = 20, offset = 0) {
  return useQuery({
    queryKey: analysisKeys.sharedWithMe(limit, offset),
    queryFn: () => analysisApi.getSharedWithMe(limit, offset),
  })
}

export function useAnalysisStats() {
  return useQuery({
    queryKey: analysisKeys.stats,
    queryFn: analysisApi.getStats,
  })
}
