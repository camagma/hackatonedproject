'use client'

import { useEffect, useState } from 'react'
import { cn } from "@/lib/utils"
import { useAppStore } from "@/lib/store"
import { AppSidebar } from "./sidebar"

interface AppLayoutProps {
  children: React.ReactNode
}

export function AppLayout({ children }: AppLayoutProps) {
  const { sidebarCollapsed, isAuthenticated } = useAppStore()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-8 h-8 rounded-lg bg-primary animate-pulse" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <>{children}</>
  }

  return (
    <div className="min-h-screen bg-background">
      <AppSidebar />
      <main
        className={cn(
          "transition-all duration-300 min-h-screen",
          sidebarCollapsed ? "ml-[72px]" : "ml-60"
        )}
      >
        {children}
      </main>
    </div>
  )
}
