import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const priorityBadgeVariants = cva(
  "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-semibold uppercase tracking-wide",
  {
    variants: {
      priority: {
        critical: "bg-critical-dim text-critical border border-critical/30",
        high: "bg-high-dim text-high border border-high/30",
        medium: "bg-medium-dim text-medium border border-medium/30",
        low: "bg-low-dim text-low border border-low/30",
      },
    },
    defaultVariants: {
      priority: "medium",
    },
  }
)

const statusBadgeVariants = cva(
  "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-semibold uppercase tracking-wide",
  {
    variants: {
      status: {
        online: "bg-online-dim text-online border border-online/30",
        offline: "bg-offline-dim text-offline border border-offline/30",
        unknown: "bg-unknown-dim text-unknown border border-unknown/30",
        info: "bg-info-dim text-info border border-info/30",
        neutral: "bg-muted text-muted-foreground border border-border",
      },
    },
    defaultVariants: {
      status: "neutral",
    },
  }
)

interface PriorityBadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof priorityBadgeVariants> {
  score?: number
}

export function PriorityBadge({ className, priority, score, children, ...props }: PriorityBadgeProps) {
  return (
    <span className={cn(priorityBadgeVariants({ priority }), className)} {...props}>
      {children || priority?.toUpperCase()}
      {score !== undefined && <span className="opacity-75">{score}</span>}
    </span>
  )
}

interface StatusBadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof statusBadgeVariants> {}

export function StatusBadge({ className, status, children, ...props }: StatusBadgeProps) {
  return (
    <span className={cn(statusBadgeVariants({ status }), className)} {...props}>
      {children}
    </span>
  )
}

interface OnlineBadgeProps {
  status: 'online' | 'offline' | 'unknown'
  lastPing?: Date
  className?: string
}

export function OnlineBadge({ status, lastPing, className }: OnlineBadgeProps) {
  const getTimeDiff = (date: Date) => {
    const diff = Math.floor((Date.now() - date.getTime()) / 1000)
    if (diff < 60) return `${diff}s`
    if (diff < 3600) return `${Math.floor(diff / 60)}m`
    return `${Math.floor(diff / 3600)}h`
  }

  const dotColor = status === 'online' ? 'bg-online' : status === 'offline' ? 'bg-offline' : 'bg-unknown'
  const bgColor = status === 'online' ? 'bg-online-dim' : status === 'offline' ? 'bg-offline-dim' : 'bg-unknown-dim'
  const textColor = status === 'online' ? 'text-online' : status === 'offline' ? 'text-offline' : 'text-unknown'

  return (
    <span className={cn(
      "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium uppercase",
      bgColor,
      textColor,
      className
    )}>
      <span className={cn("w-1.5 h-1.5 rounded-full animate-pulse", dotColor)} />
      {status.toUpperCase()}
      {lastPing && <span className="opacity-75">{getTimeDiff(lastPing)}</span>}
    </span>
  )
}

interface CaseIdBadgeProps {
  caseId: string
  className?: string
}

export function CaseIdBadge({ caseId, className }: CaseIdBadgeProps) {
  return (
    <span className={cn(
      "inline-flex items-center px-2 py-0.5 rounded bg-muted text-muted-foreground text-[10px] font-mono font-medium",
      className
    )}>
      {caseId}
    </span>
  )
}
