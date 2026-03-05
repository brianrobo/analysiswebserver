import { Sun, Moon, User } from 'lucide-react'
import { useCurrentUser } from '@/hooks/useAuth'
import { useUpdateTheme } from '@/hooks/useSettings'
import { useThemeStore } from '@/stores/themeStore'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'

const roleLabels: Record<string, string> = {
  admin: '관리자',
  team_lead: '팀 리더',
  member: '멤버',
  viewer: '뷰어',
}

export function SettingsPage() {
  const { data: user } = useCurrentUser()
  const updateTheme = useUpdateTheme()
  const theme = useThemeStore((s) => s.theme)

  const handleThemeToggle = (checked: boolean) => {
    updateTheme.mutate(checked ? 'dark' : 'light')
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">설정</h1>
        <p className="text-muted-foreground mt-1">계정 및 앱 환경 설정</p>
      </div>

      {/* Account Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />계정 정보
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {user ? (
            <>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">이메일</p>
                  <p className="font-medium">{user.email}</p>
                </div>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">이름</p>
                  <p className="font-medium">{user.full_name ?? '-'}</p>
                </div>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">역할</p>
                  <Badge variant="secondary" className="mt-1">
                    {roleLabels[user.role] ?? user.role}
                  </Badge>
                </div>
              </div>
              {user.team_id && (
                <>
                  <Separator />
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">팀 ID</p>
                      <p className="font-medium">{user.team_id}</p>
                    </div>
                  </div>
                </>
              )}
            </>
          ) : (
            <p className="text-muted-foreground text-sm">로딩 중...</p>
          )}
        </CardContent>
      </Card>

      {/* Appearance */}
      <Card>
        <CardHeader>
          <CardTitle>화면 설정</CardTitle>
          <CardDescription>앱 테마를 변경합니다.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {theme === 'dark' ? (
                <Moon className="h-5 w-5 text-primary" />
              ) : (
                <Sun className="h-5 w-5 text-primary" />
              )}
              <div>
                <Label htmlFor="theme-toggle" className="cursor-pointer">
                  다크 모드
                </Label>
                <p className="text-sm text-muted-foreground">
                  현재: {theme === 'dark' ? '다크 모드' : '라이트 모드'}
                </p>
              </div>
            </div>
            <Switch
              id="theme-toggle"
              checked={theme === 'dark'}
              onCheckedChange={handleThemeToggle}
              disabled={updateTheme.isPending}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
