import { cn } from "@/lib/utils"
import type { VolunteerStatus } from "@/lib/store"

interface VolunteerAvatarProps {
  name: string
  status?: VolunteerStatus
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function VolunteerAvatar({ name, status = 'offline', size = 'md', className }: VolunteerAvatarProps) {
  const initials = name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)

  const sizeClasses = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-12 h-12 text-base',
  }

  const statusColors = {
    active: 'bg-online-dim text-online border-online/30',
    busy: 'bg-high-dim text-high border-high/30',
    offline: 'bg-muted text-muted-foreground border-border',
  }

  return (
    <div
      className={cn(
        "inline-flex items-center justify-center rounded-lg font-mono font-bold border",
        sizeClasses[size],
        statusColors[status],
        className
      )}
    >
      {initials}
    </div>
  )
}

interface UserAvatarProps {
  name: string
  role: 'volunteer' | 'reporter'
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function UserAvatar({ name, role, size = 'md', className }: UserAvatarProps) {
  const initials = name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)

  const sizeClasses = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-12 h-12 text-base',
  }

  return (
    <div
      className={cn(
        "inline-flex items-center justify-center rounded-lg font-mono font-bold",
        role === 'volunteer' ? 'bg-primary/10 text-primary' : 'bg-info-dim text-info',
        sizeClasses[size],
        className
      )}
    >
      {initials}
    </div>
  )
}
