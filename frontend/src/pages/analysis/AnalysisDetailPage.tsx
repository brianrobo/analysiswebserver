import { useParams, useNavigate } from 'react-router-dom'
import { useCallback, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import { toast } from 'sonner'
import type { AxiosError } from 'axios'
import { ArrowLeft, Download, Share2, AlertTriangle, Clock } from 'lucide-react'
import { useAnalysisStatus, useAnalysisResult, analysisKeys } from '@/hooks/useAnalysis'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useCurrentUser } from '@/hooks/useAuth'
import { ProgressBar } from '@/components/analysis/ProgressBar'
import { ResultViewer } from '@/components/analysis/ResultViewer'
import { ShareDialog } from '@/components/sharing/ShareDialog'
import { analysisApi } from '@/api/analysis.api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import type { ApiError } from '@/api/types'

export function AnalysisDetailPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data: user } = useCurrentUser()
  const [shareOpen, setShareOpen] = useState(false)
  const [isDownloading, setIsDownloading] = useState(false)

  const jobIdNum = Number(jobId)

  const { data: job, isLoading: jobLoading } = useAnalysisStatus(jobIdNum, !!jobId)

  const isActiveJob = job?.status === 'pending' || job?.status === 'running'
  const isCompleted = job?.status === 'completed'

  // WebSocket: only connect when job is active
  const onCompleted = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: analysisKeys.result(jobIdNum) })
    queryClient.invalidateQueries({ queryKey: ['analysis', 'history'] })
  }, [queryClient, jobIdNum])

  const wsState = useWebSocket(jobIdNum, isActiveJob, onCompleted)

  const { data: result, isLoading: resultLoading } = useAnalysisResult(
    jobIdNum,
    isCompleted || wsState.status === 'completed'
  )

  const canShare = user?.role === 'admin' || user?.role === 'team_lead'

  const handleDownload = async (format: 'json' | 'csv' | 'zip') => {
    if (!job) return
    setIsDownloading(true)
    try {
      const ext = format === 'zip' ? 'zip' : format
      const filename = `analysis_${jobIdNum}_${job.job_name.replace(/[^a-zA-Z0-9]/g, '_')}.${ext}`
      await analysisApi.downloadFile(jobIdNum, format, filename)
      toast.success(`${format.toUpperCase()} 파일 다운로드가 시작되었습니다.`)
    } catch (error: unknown) {
      const axiosError = error as AxiosError<ApiError>
      toast.error(axiosError.response?.data?.detail ?? '다운로드에 실패했습니다.')
    } finally {
      setIsDownloading(false)
    }
  }

  if (jobLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (!job) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 mx-auto mb-3 text-destructive opacity-50" />
        <p className="text-muted-foreground">분석을 찾을 수 없습니다.</p>
        <Button variant="link" onClick={() => navigate('/dashboard')}>대시보드로 돌아가기</Button>
      </div>
    )
  }

  const displayProgress = wsState.progress > 0 ? wsState.progress : job.progress
  const displayStatus = wsState.status ?? job.status
  const displayMessage = wsState.message

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate('/dashboard')}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">{job.job_name}</h1>
            <p className="text-sm text-muted-foreground flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {format(new Date(job.created_at), 'yyyy년 MM월 dd일 HH:mm', { locale: ko })}
            </p>
          </div>
        </div>

        {isCompleted && result && (
          <div className="flex items-center gap-2">
            {canShare && (
              <Button variant="outline" onClick={() => setShareOpen(true)}>
                <Share2 className="h-4 w-4 mr-2" />
                공유
              </Button>
            )}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button disabled={isDownloading}>
                  <Download className="h-4 w-4 mr-2" />
                  {isDownloading ? '다운로드 중...' : '다운로드'}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => handleDownload('json')}>JSON 형식</DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleDownload('csv')}>CSV 형식</DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleDownload('zip')}>ZIP (순수 함수 추출)</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )}
      </div>

      {/* Progress View (Active Jobs) */}
      {(isActiveJob || displayStatus === 'running' || displayStatus === 'pending') && (
        <Card>
          <CardHeader>
            <CardTitle>분석 진행 중</CardTitle>
          </CardHeader>
          <CardContent>
            <ProgressBar
              progress={displayProgress}
              status={displayStatus}
              message={displayMessage}
            />
            {wsState.isConnected && (
              <p className="text-xs text-green-600 mt-3">● 실시간 업데이트 연결됨</p>
            )}
            {!wsState.isConnected && isActiveJob && (
              <p className="text-xs text-muted-foreground mt-3">⚠ 실시간 연결 끊김 (5초마다 새로고침)</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Error View */}
      {(job.status === 'failed' || wsState.error) && (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              분석 실패
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{job.error_message ?? wsState.error ?? '알 수 없는 오류가 발생했습니다.'}</p>
          </CardContent>
        </Card>
      )}

      {/* Result View */}
      {resultLoading && isCompleted && (
        <div className="space-y-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      )}

      {result && (
        <ResultViewer result={result.result_data} />
      )}

      {/* Share Dialog */}
      <ShareDialog
        open={shareOpen}
        onOpenChange={setShareOpen}
        jobId={jobIdNum}
      />
    </div>
  )
}
