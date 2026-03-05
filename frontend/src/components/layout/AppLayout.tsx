import { Outlet } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'
import { useCurrentUser } from '@/hooks/useAuth'
import { useSettings } from '@/hooks/useSettings'
import { useThemeStore } from '@/stores/themeStore'

export function AppLayout() {
  const { data: settings } = useSettings()
  const { } = useCurrentUser() // triggers user fetch on mount
  const setTheme = useThemeStore((s) => s.setTheme)

  const [collapsed, setCollapsed] = useState(false)

  // Apply saved settings on mount
  useEffect(() => {
    if (settings) {
      setCollapsed(settings.sidebar_collapsed)
      setTheme(settings.theme)
    }
  }, [settings, setTheme])

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />
      <div className="flex flex-col flex-1 overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-auto p-6 bg-background">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
