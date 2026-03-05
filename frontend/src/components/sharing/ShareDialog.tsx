import { useState } from 'react'
import { toast } from 'sonner'
import type { AxiosError } from 'axios'
import { useShareAnalysis } from '@/hooks/useAnalysis'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Switch } from '@/components/ui/switch'
import type { ApiError } from '@/api/types'

interface ShareDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  jobId: number
}

export function ShareDialog({ open, onOpenChange, jobId }: ShareDialogProps) {
  const [teamId, setTeamId] = useState('')
  const [canView, setCanView] = useState(true)
  const [canDownload, setCanDownload] = useState(true)
  const [expiresAt, setExpiresAt] = useState('')
  const shareAnalysis = useShareAnalysis()

  const handleSubmit = () => {
    const teamIdNum = parseInt(teamId, 10)
    if (!teamId || isNaN(teamIdNum)) {
      toast.error('유효한 팀 ID를 입력해주세요.')
      return
    }

    shareAnalysis.mutate(
      {
        jobId,
        request: {
          team_id: teamIdNum,
          can_view: canView,
          can_download: canDownload,
          expires_at: expiresAt ? new Date(expiresAt).toISOString() : null,
        },
      },
      {
        onSuccess: () => {
          toast.success('분석이 공유되었습니다.')
          onOpenChange(false)
          setTeamId('')
          setExpiresAt('')
        },
        onError: (error: unknown) => {
          const axiosError = error as AxiosError<ApiError>
          toast.error(axiosError.response?.data?.detail ?? '공유에 실패했습니다.')
        },
      }
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>팀과 공유</DialogTitle>
          <DialogDescription>팀 ID를 입력하여 분석 결과를 공유하세요.</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="team-id">팀 ID</Label>
            <Input
              id="team-id"
              type="number"
              placeholder="팀 ID 입력"
              value={teamId}
              onChange={(e) => setTeamId(e.target.value)}
            />
          </div>
          <div className="flex items-center justify-between">
            <Label htmlFor="can-view">보기 권한</Label>
            <Switch id="can-view" checked={canView} onCheckedChange={setCanView} />
          </div>
          <div className="flex items-center justify-between">
            <Label htmlFor="can-download">다운로드 권한</Label>
            <Switch id="can-download" checked={canDownload} onCheckedChange={setCanDownload} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="expires-at">만료일 (선택)</Label>
            <Input
              id="expires-at"
              type="datetime-local"
              value={expiresAt}
              onChange={(e) => setExpiresAt(e.target.value)}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>취소</Button>
          <Button onClick={handleSubmit} disabled={shareAnalysis.isPending}>
            {shareAnalysis.isPending ? '공유 중...' : '공유하기'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
