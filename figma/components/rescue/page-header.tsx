'use client'

import { useEffect, useState } from 'react'
import { cn } from "@/lib/utils"

interface PageHeaderProps {
  title: string
  showTimestamp?: boolean
  children?: React.ReactNode
  className?: string
}

export function PageHeader({ title, showTimestamp = false, children, className }: PageHeaderProps) {
  const [time, setTime] = useState<string>('')

  useEffect(() => {
    const updateTime = () => {
      const now = new Date()
      setTime(now.toLocaleString('en-US', {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      }))
    }
    
    updateTime()
    const interval = setInterval(updateTime, 1000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className={cn("flex items-center justify-between", className)}>
      <div>
        <h1 className="text-2xl font-sans font-extrabold text-foreground">{title}</h1>
        {showTimestamp && time && (
          <p className="text-xs font-mono text-muted-foreground mt-0.5">{time}</p>
        )}
      </div>
      {children}
    </div>
  )
}

interface SectionHeaderProps {
  label: string
  className?: string
}

export function SectionHeader({ label, className }: SectionHeaderProps) {
  return (
    <div className={cn("flex items-center gap-4 mb-4", className)}>
      <h2 className="text-sm font-sans font-bold text-foreground uppercase tracking-wide shrink-0">{label}</h2>
      <div className="flex-1 h-px bg-border" />
    </div>
  )
}
