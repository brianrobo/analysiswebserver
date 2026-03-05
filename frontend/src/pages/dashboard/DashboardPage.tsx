import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import { PlusCircle, Trash2, Eye, BarChart3, CheckCircle2, Loader2, XCircle } from 'lucide-react'
import { toast } from 'sonner'
import type { AxiosError } from 'axios'
import { useAnalysisHistory, useDeleteAnalysis, useAnalysisStats } from '@/hooks/useAnalysis'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import type { JobStatus, ApiError } from '@/api/types'

const statusConfig: Record<JobStatus, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: React.ComponentType<{ className?: string }> }> = {
  pending: { label: '대기 중', variant: 'outline', icon: Loader2 },
  running: { label: '분석 중', variant: 'secondary', icon: Loader2 },
  completed: { label: '완료', variant: 'default', icon: CheckCircle2 },
  failed: { label: '실패', variant: 'destructive', icon: XCircle },
  cancelled: { label: '취소됨', variant: 'outline', icon: XCircle },
}

export function DashboardPage() {
  const navigate = useNavigate()
  const { data: history, isLoading } = useAnalysisHistory()
  const { data: stats } = useAnalysisStats()
  const deleteJob = useDeleteAnalysis()
  const [deleteTargetId, setDeleteTargetId] = useState<number | null>(null)

  const handleDelete = () => {
    if (deleteTargetId === null) return
    deleteJob.mutate(deleteTargetId, {
      onSuccess: () => {
        toast.success('분석이 삭제되었습니다.')
        setDeleteTargetId(null)
      },
      onError: (error: unknown) => {
        const axiosError = error as AxiosError<ApiError>
        toast.error(axiosError.response?.data?.detail ?? '삭제에 실패했습니다.')
        setDeleteTargetId(null)
      },
    })
  }

  const totalJobs = history?.length ?? 0
  const completedJobs = history?.filter((j) => j.status === 'completed').length ?? 0
  const runningJobs = history?.filter((j) => j.status === 'running' || j.status === 'pending').length ?? 0
  const cacheStats = (stats as { cache_stats?: { hit_rate?: number } } | undefined)?.cache_stats

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">대시보드</h1>
        <Button onClick={() => navigate('/analysis/new')}>
          <PlusCircle className="h-4 w-4 mr-2" />
          새 분석 시작
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <BarChart3 className="h-4 w-4" /> 전체 분석
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{totalJobs}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-500" /> 완료
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-green-600">{completedJobs}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Loader2 className="h-4 w-4 text-blue-500" /> 진행 중
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-blue-600">{runningJobs}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">캐시 히트율</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {cacheStats?.hit_rate != null ? `${(cacheStats.hit_rate * 100).toFixed(0)}%` : '-'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* History Table */}
      <Card>
        <CardHeader>
          <CardTitle>분석 히스토리</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : !history || history.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <BarChart3 className="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p>아직 분석 기록이 없습니다.</p>
              <Button variant="link" onClick={() => navigate('/analysis/new')}>
                첫 번째 분석을 시작해보세요
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>분석 이름</TableHead>
                  <TableHead>상태</TableHead>
                  <TableHead>입력 파일</TableHead>
                  <TableHead>생성일</TableHead>
                  <TableHead className="text-right">작업</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {history.map((job) => {
                  const config = statusConfig[job.status] ?? statusConfig.pending
                  const StatusIcon = config.icon
                  return (
                    <TableRow
                      key={job.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => navigate(`/analysis/${job.id}`)}
                    >
                      <TableCell className="font-medium">{job.job_name}</TableCell>
                      <TableCell>
                        <Badge variant={config.variant} className="flex items-center gap-1 w-fit">
                          <StatusIcon className={`h-3 w-3 ${(job.status === 'running' || job.status === 'pending') ? 'animate-spin' : ''}`} />
                          {config.label}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-muted-foreground text-sm">
                        {job.input_file ? job.input_file.split('/').pop() ?? job.input_file : '-'}
                      </TableCell>
                      <TableCell className="text-muted-foreground text-sm">
                        {format(new Date(job.created_at), 'yyyy.MM.dd HH:mm', { locale: ko })}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1" onClick={(e) => e.stopPropagation()}>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => navigate(`/analysis/${job.id}`)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setDeleteTargetId(job.id)}
                            className="text-destructive hover:text-destructive"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteTargetId !== null} onOpenChange={(open) => !open && setDeleteTargetId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>분석 삭제</DialogTitle>
            <DialogDescription>
              이 분석을 삭제하면 결과 데이터도 함께 삭제됩니다. 계속하시겠습니까?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTargetId(null)}>취소</Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteJob.isPending}
            >
              {deleteJob.isPending ? '삭제 중...' : '삭제'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
