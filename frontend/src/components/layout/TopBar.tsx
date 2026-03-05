import { Sun, Moon, User, LogOut } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Badge } from '@/components/ui/badge'
import { useCurrentUser, useLogout } from '@/hooks/useAuth'
import { useUpdateTheme } from '@/hooks/useSettings'
import { useThemeStore } from '@/stores/themeStore'

const roleLabels: Record<string, string> = {
  admin: '관리자',
  team_lead: '팀 리더',
  member: '멤버',
  viewer: '뷰어',
}

export function TopBar() {
  const { data: user } = useCurrentUser()
  const logout = useLogout()
  const updateTheme = useUpdateTheme()
  const theme = useThemeStore((s) => s.theme)

  const handleThemeToggle = () => {
    updateTheme.mutate(theme === 'dark' ? 'light' : 'dark')
  }

  return (
    <header className="h-14 border-b flex items-center justify-between px-4 bg-background">
      <div />
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={handleThemeToggle}
          title={theme === 'dark' ? '라이트 모드로 전환' : '다크 모드로 전환'}
        >
          {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="gap-2">
              <User className="h-4 w-4" />
              <span className="text-sm">{user?.email ?? '...'}</span>
              {user && (
                <Badge variant="secondary" className="text-xs">
                  {roleLabels[user.role] ?? user.role}
                </Badge>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>{user?.full_name ?? user?.email}</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={logout} className="text-destructive">
              <LogOut className="h-4 w-4 mr-2" />
              로그아웃
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
