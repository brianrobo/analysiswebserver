import { useNavigate } from 'react-router-dom'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import { Share2, Eye, Download } from 'lucide-react'
import { useSharedWithMe } from '@/hooks/useAnalysis'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

export function SharedWithMePage() {
  const navigate = useNavigate()
  const { data: sharedItems, isLoading } = useSharedWithMe()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">공유된 분석</h1>
        <p className="text-muted-foreground mt-1">다른 팀원이 나와 공유한 분석 목록입니다.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Share2 className="h-5 w-5" />공유 목록
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : !sharedItems || sharedItems.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Share2 className="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p>공유된 분석이 없습니다.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>분석 이름</TableHead>
                  <TableHead>소유자</TableHead>
                  <TableHead>권한</TableHead>
                  <TableHead>공유일</TableHead>
                  <TableHead>만료일</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sharedItems.map((item) => (
                  <TableRow
                    key={item.job_id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => navigate(`/analysis/${item.job_id}`)}
                  >
                    <TableCell className="font-medium">
                      {item.job_name ?? `분석 #${item.job_id}`}
                    </TableCell>
                    <TableCell className="text-muted-foreground">{item.owner_name}</TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        {item.share.can_view && (
                          <Badge variant="secondary" className="flex items-center gap-1">
                            <Eye className="h-3 w-3" />보기
                          </Badge>
                        )}
                        {item.share.can_download && (
                          <Badge variant="secondary" className="flex items-center gap-1">
                            <Download className="h-3 w-3" />다운로드
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {format(new Date(item.share.shared_at), 'yyyy.MM.dd', { locale: ko })}
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {item.share.expires_at
                        ? format(new Date(item.share.expires_at), 'yyyy.MM.dd', { locale: ko })
                        : '만료 없음'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
