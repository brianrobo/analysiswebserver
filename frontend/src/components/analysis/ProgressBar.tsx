import { Progress } from '@/components/ui/progress'
import { Loader2 } from 'lucide-react'
import type { JobStatus } from '@/api/types'

interface ProgressBarProps {
  progress: number
  status: JobStatus | null
  message?: string
}

export function ProgressBar({ progress, status, message }: ProgressBarProps) {
  const isRunning = status === 'running' || status === 'pending'

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isRunning && <Loader2 className="h-4 w-4 animate-spin text-primary" />}
          <span className="text-sm font-medium">
            {status === 'pending' ? '분석 대기 중...' : status === 'running' ? '분석 중...' : '완료'}
          </span>
        </div>
        <span className="text-sm font-bold text-primary">{progress}%</span>
      </div>
      <Progress value={progress} className="h-3" />
      {message && (
        <p className="text-sm text-muted-foreground">{message}</p>
      )}
    </div>
  )
}
