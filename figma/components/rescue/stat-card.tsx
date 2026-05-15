'use client'

import { cn } from "@/lib/utils"

interface StatCardProps {
  label: string
  value: string | number
  subtitle?: string
  color: 'red' | 'orange' | 'green' | 'blue' | 'gray'
  className?: string
}

export function StatCard({ label, value, subtitle, color, className }: StatCardProps) {
  const colorClasses = {
    red: 'border-t-critical',
    orange: 'border-t-high',
    green: 'border-t-online',
    blue: 'border-t-info',
    gray: 'border-t-muted-foreground',
  }

  return (
    <div className={cn(
      "bg-card rounded-xl border border-t-[3px] p-4",
      colorClasses[color],
      className
    )}>
      <p className="text-xs font-mono text-muted-foreground uppercase tracking-wide mb-1">{label}</p>
      <p className="text-3xl font-mono font-bold text-foreground">{value}</p>
      {subtitle && (
        <p className="text-xs font-mono text-muted-foreground mt-1">{subtitle}</p>
      )}
    </div>
  )
}

interface MiniStatCardProps {
  label: string
  value: string | number
  color: 'red' | 'green'
  className?: string
}

export function MiniStatCard({ label, value, color, className }: MiniStatCardProps) {
  const colorClasses = {
    red: 'text-critical',
    green: 'text-online',
  }

  return (
    <div className={cn("bg-card rounded-lg border p-3", className)}>
      <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-wide">{label}</p>
      <p className={cn("text-xl font-mono font-bold", colorClasses[color])}>{value}</p>
    </div>
  )
}
