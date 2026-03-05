import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import type { ProjectAnalysisResult } from '@/api/types'
import { FileCode2, Zap, AlertCircle, ArrowRight } from 'lucide-react'

interface ResultViewerProps {
  result: ProjectAnalysisResult
}

const classificationConfig = {
  ui: { label: 'UI', variant: 'destructive' as const },
  logic: { label: '로직', variant: 'default' as const },
  mixed: { label: '혼합', variant: 'secondary' as const },
}

const priorityConfig = {
  high: { label: '높음', variant: 'destructive' as const },
  medium: { label: '중간', variant: 'secondary' as const },
  low: { label: '낮음', variant: 'outline' as const },
}

function getReadinessColor(percent: number): string {
  if (percent >= 80) return 'text-green-600'
  if (percent >= 60) return 'text-yellow-600'
  return 'text-red-600'
}

export function ResultViewer({ result }: ResultViewerProps) {
  const summary = result.analysis_summary

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">전체 파일</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{summary.total_files}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">전체 코드 라인</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{summary.total_loc.toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">순수 함수</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{summary.pure_functions_count}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">웹 변환 가능성</CardTitle>
          </CardHeader>
          <CardContent>
            <p className={`text-2xl font-bold ${getReadinessColor(summary.web_readiness_percent)}`}>
              {summary.web_readiness_percent.toFixed(1)}%
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Web Readiness Progress */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />웹 변환 가능성
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex justify-between text-sm">
            <span>전체 점수</span>
            <span className={`font-bold ${getReadinessColor(summary.web_readiness_percent)}`}>
              {summary.web_readiness_percent.toFixed(1)}%
            </span>
          </div>
          <Progress value={summary.web_readiness_percent} className="h-4" />
          <div className="grid grid-cols-3 gap-4 pt-2 text-center text-sm">
            <div>
              <p className="text-2xl font-bold text-red-500">{summary.ui_files}</p>
              <p className="text-muted-foreground">UI 파일</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-blue-500">{summary.logic_files}</p>
              <p className="text-muted-foreground">로직 파일</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-yellow-500">{summary.mixed_files}</p>
              <p className="text-muted-foreground">혼합 파일</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* File Analysis Table */}
      {result.file_analyses.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileCode2 className="h-5 w-5" />파일 분석 결과
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>파일 경로</TableHead>
                  <TableHead className="text-right">LOC</TableHead>
                  <TableHead className="text-right">UI %</TableHead>
                  <TableHead>분류</TableHead>
                  <TableHead className="text-right">순수 함수</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {result.file_analyses.map((file) => {
                  const classConfig = classificationConfig[file.classification] ?? classificationConfig.mixed
                  return (
                    <TableRow key={file.file_path}>
                      <TableCell className="font-mono text-xs max-w-xs truncate">
                        {file.file_path}
                      </TableCell>
                      <TableCell className="text-right">{file.loc}</TableCell>
                      <TableCell className="text-right">{(file.ui_ratio * 100).toFixed(0)}%</TableCell>
                      <TableCell>
                        <Badge variant={classConfig.variant}>{classConfig.label}</Badge>
                      </TableCell>
                      <TableCell className="text-right">{file.pure_functions.length}</TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Extraction Suggestions */}
      {result.extraction_suggestions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ArrowRight className="h-5 w-5" />추출 제안
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {result.extraction_suggestions.map((sug, i) => (
                <div key={i} className="flex items-start gap-3 p-3 bg-muted/30 rounded-lg">
                  <code className="text-xs bg-muted px-2 py-1 rounded font-mono shrink-0">
                    {sug.function_name}
                  </code>
                  <div className="min-w-0">
                    <p className="text-xs text-muted-foreground font-mono truncate">{sug.file_path}</p>
                    <p className="text-sm mt-1">{sug.reason}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Refactoring Suggestions */}
      {result.refactoring_suggestions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5" />리팩토링 제안
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {result.refactoring_suggestions.map((sug, i) => {
                const priConfig = priorityConfig[sug.priority] ?? priorityConfig.low
                return (
                  <div key={i} className="flex items-start gap-3 p-3 bg-muted/30 rounded-lg">
                    <Badge variant={priConfig.variant} className="shrink-0 mt-0.5">{priConfig.label}</Badge>
                    <div>
                      <p className="text-xs text-muted-foreground font-mono">{sug.file_path}</p>
                      <p className="text-sm mt-1">{sug.suggestion}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Web Conversion Guide */}
      {result.web_conversion_guide && (
        <Card>
          <CardHeader>
            <CardTitle>웹 변환 가이드</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-4">
              <div>
                <p className="text-sm text-muted-foreground">권장 프레임워크</p>
                <Badge variant="default" className="mt-1">{result.web_conversion_guide.recommended_framework}</Badge>
              </div>
              <Separator orientation="vertical" />
              <div>
                <p className="text-sm text-muted-foreground">예상 작업량</p>
                <p className="font-medium mt-1">{result.web_conversion_guide.estimated_effort}</p>
              </div>
            </div>
            <div>
              <p className="text-sm font-medium mb-2">변환 단계</p>
              <ol className="space-y-2">
                {result.web_conversion_guide.steps.map((step, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="bg-primary text-primary-foreground rounded-full h-5 w-5 flex items-center justify-center text-xs shrink-0 mt-0.5">
                      {i + 1}
                    </span>
                    <span className="text-sm">{step}</span>
                  </li>
                ))}
              </ol>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
