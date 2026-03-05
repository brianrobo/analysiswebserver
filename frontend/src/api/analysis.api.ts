import { apiClient } from './client'
import type {
  AnalysisJobResponse,
  AnalysisHistoryItem,
  AnalysisResultResponse,
  ShareRequest,
  ShareResponse,
  SharedAnalysisItem,
} from './types'

export const analysisApi = {
  uploadFile: async (file: File, jobName?: string): Promise<AnalysisJobResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    if (jobName) formData.append('job_name', jobName)
    const { data } = await apiClient.post<AnalysisJobResponse>('/analysis/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  fromPath: async (path: string, jobName?: string): Promise<AnalysisJobResponse> => {
    const { data } = await apiClient.post<AnalysisJobResponse>('/analysis/from-path', {
      path,
      job_name: jobName,
    })
    return data
  },

  getStatus: async (jobId: number): Promise<AnalysisJobResponse> => {
    const { data } = await apiClient.get<AnalysisJobResponse>(`/analysis/${jobId}/status`)
    return data
  },

  getResult: async (jobId: number): Promise<AnalysisResultResponse> => {
    const { data } = await apiClient.get<AnalysisResultResponse>(`/analysis/${jobId}/result`)
    return data
  },

  getHistory: async (limit = 20, offset = 0): Promise<AnalysisHistoryItem[]> => {
    const { data } = await apiClient.get<AnalysisHistoryItem[]>('/analysis/history', {
      params: { limit, offset },
    })
    return data
  },

  getStats: async (): Promise<Record<string, unknown>> => {
    const { data } = await apiClient.get('/analysis/stats')
    return data as Record<string, unknown>
  },

  deleteJob: async (jobId: number): Promise<void> => {
    await apiClient.delete(`/analysis/${jobId}`)
  },

  // Download via Blob (Authorization header required - can't use plain href)
  downloadFile: async (jobId: number, format: 'json' | 'csv' | 'zip', filename: string): Promise<void> => {
    const response = await apiClient.get(`/analysis/${jobId}/download`, {
      params: { format },
      responseType: 'blob',
    })
    const url = window.URL.createObjectURL(new Blob([response.data as BlobPart]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },

  shareWithTeam: async (jobId: number, req: ShareRequest): Promise<ShareResponse> => {
    const { data } = await apiClient.post<ShareResponse>(`/analysis/${jobId}/share`, req)
    return data
  },

  unshareWithTeam: async (jobId: number, teamId: number): Promise<void> => {
    await apiClient.delete(`/analysis/${jobId}/share/${teamId}`)
  },

  getSharedWithMe: async (limit = 20, offset = 0): Promise<SharedAnalysisItem[]> => {
    const { data } = await apiClient.get<SharedAnalysisItem[]>('/analysis/shared-with-me', {
      params: { limit, offset },
    })
    return data
  },
}
