import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import type { AxiosError } from 'axios'
import { useUploadAnalysis, useFromPathAnalysis } from '@/hooks/useAnalysis'
import { FileUploadZone } from '@/components/analysis/FileUploadZone'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Label } from '@/components/ui/label'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import type { ApiError } from '@/api/types'

const pathSchema = z.object({
  path: z.string().min(1, '경로를 입력해주세요.'),
  job_name: z.string().max(200).optional(),
})

type PathFormValues = z.infer<typeof pathSchema>

export function NewAnalysisPage() {
  const navigate = useNavigate()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [fileJobName, setFileJobName] = useState('')
  const uploadAnalysis = useUploadAnalysis()
  const fromPathAnalysis = useFromPathAnalysis()

  const pathForm = useForm<PathFormValues>({
    resolver: zodResolver(pathSchema),
    defaultValues: { path: '', job_name: '' },
  })

  const handleFileSubmit = () => {
    if (!selectedFile) return
    uploadAnalysis.mutate(
      { file: selectedFile, jobName: fileJobName || undefined },
      {
        onSuccess: (job) => {
          toast.success(`분석이 시작되었습니다: ${job.job_name}`)
          navigate(`/analysis/${job.id}`)
        },
        onError: (error: unknown) => {
          const axiosError = error as AxiosError<ApiError>
          toast.error(axiosError.response?.data?.detail ?? '업로드에 실패했습니다.')
        },
      }
    )
  }

  const handlePathSubmit = (data: PathFormValues) => {
    fromPathAnalysis.mutate(
      { path: data.path, jobName: data.job_name || undefined },
      {
        onSuccess: (job) => {
          toast.success(`분석이 시작되었습니다: ${job.job_name}`)
          navigate(`/analysis/${job.id}`)
        },
        onError: (error: unknown) => {
          const axiosError = error as AxiosError<ApiError>
          toast.error(axiosError.response?.data?.detail ?? '분석 시작에 실패했습니다.')
        },
      }
    )
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">새 분석 시작</h1>
        <p className="text-muted-foreground mt-1">PyQt 프로젝트를 분석하여 웹 변환 가능성을 확인합니다.</p>
      </div>

      <Tabs defaultValue="upload">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="upload">파일 업로드</TabsTrigger>
          <TabsTrigger value="path">로컬 경로</TabsTrigger>
        </TabsList>

        {/* Tab 1: File Upload */}
        <TabsContent value="upload">
          <Card>
            <CardHeader>
              <CardTitle>파일 업로드</CardTitle>
              <CardDescription>.py 파일 또는 .zip 압축 파일을 업로드하세요.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <FileUploadZone
                onFileSelect={setSelectedFile}
                selectedFile={selectedFile}
                onClear={() => setSelectedFile(null)}
              />
              <div className="space-y-2">
                <Label htmlFor="file-job-name">분석 이름 (선택)</Label>
                <Input
                  id="file-job-name"
                  placeholder="예: MyApp 분석"
                  value={fileJobName}
                  onChange={(e) => setFileJobName(e.target.value)}
                  maxLength={200}
                />
              </div>
              <Button
                className="w-full"
                disabled={!selectedFile || uploadAnalysis.isPending}
                onClick={handleFileSubmit}
              >
                {uploadAnalysis.isPending ? '업로드 중...' : '분석 시작'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 2: Local Path */}
        <TabsContent value="path">
          <Card>
            <CardHeader>
              <CardTitle>로컬 경로 분석</CardTitle>
              <CardDescription>서버에서 접근 가능한 로컬 파일 또는 디렉토리 경로를 입력하세요.</CardDescription>
            </CardHeader>
            <CardContent>
              <Form {...pathForm}>
                <form onSubmit={pathForm.handleSubmit(handlePathSubmit)} className="space-y-4">
                  <FormField
                    control={pathForm.control}
                    name="path"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>경로</FormLabel>
                        <FormControl>
                          <Input
                            placeholder="C:/Users/username/my-pyqt-project"
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={pathForm.control}
                    name="job_name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>분석 이름 (선택)</FormLabel>
                        <FormControl>
                          <Input placeholder="예: MyApp 분석" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <Button
                    type="submit"
                    className="w-full"
                    disabled={fromPathAnalysis.isPending}
                  >
                    {fromPathAnalysis.isPending ? '시작 중...' : '분석 시작'}
                  </Button>
                </form>
              </Form>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
