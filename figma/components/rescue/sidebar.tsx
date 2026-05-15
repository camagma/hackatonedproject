'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useTheme } from 'next-themes'
import { cn } from "@/lib/utils"
import { useAppStore, type WeatherCondition } from "@/lib/store"
import { UserAvatar } from "./avatars"
import { MiniStatCard } from "./stat-card"
import { Button } from "@/components/ui/button"
import {
  LayoutDashboard,
  Target,
  FileText,
  Users,
  UserCircle,
  MapPin,
  Bot,
  AlertCircle,
  Plus,
  LogOut,
  Sun,
  Moon,
  Cloud,
  CloudRain,
  CloudLightning,
  Snowflake,
  CloudFog,
  Thermometer,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'

const weatherIcons: Record<WeatherCondition, React.ReactNode> = {
  clear: <Sun className="w-4 h-4" />,
  rain: <CloudRain className="w-4 h-4" />,
  storm: <CloudLightning className="w-4 h-4" />,
  snow: <Snowflake className="w-4 h-4" />,
  fog: <CloudFog className="w-4 h-4" />,
  extreme_heat: <Thermometer className="w-4 h-4" />,
}

const weatherLabels: Record<WeatherCondition, string> = {
  clear: 'Clear',
  rain: 'Rain',
  storm: 'Storm',
  snow: 'Snow',
  fog: 'Fog',
  extreme_heat: 'Extreme Heat',
}

const volunteerNavItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/missions', label: 'My Missions', icon: Target },
  { href: '/cases', label: 'All Cases', icon: FileText },
  { href: '/teams', label: 'Teams', icon: Users },
  { href: '/volunteers', label: 'Volunteers', icon: UserCircle },
  { href: '/tracking', label: 'Tracking', icon: MapPin },
  { href: '/ai-log', label: 'AI Log', icon: Bot },
]

const reporterNavItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/report', label: 'Report Missing', icon: AlertCircle },
  { href: '/my-reports', label: 'My Reports', icon: FileText },
]

export function AppSidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)
  
  const {
    currentUser,
    isAuthenticated,
    weatherCondition,
    setWeatherCondition,
    sidebarCollapsed,
    toggleSidebar,
    cases,
    volunteers,
    logout,
  } = useAppStore()

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted || !isAuthenticated || !currentUser) return null

  const navItems = currentUser.role === 'volunteer' ? volunteerNavItems : reporterNavItems
  const activeCases = cases.filter(c => c.status === 'active' || c.status === 'assigned').length
  const onlineVolunteers = volunteers.filter(v => v.status === 'active').length

  const handleLogout = () => {
    logout()
    router.push('/')
  }

  const weatherConditions: WeatherCondition[] = ['clear', 'rain', 'storm', 'snow', 'fog', 'extreme_heat']

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 h-screen bg-sidebar border-r border-sidebar-border flex flex-col transition-all duration-300 z-50",
        sidebarCollapsed ? "w-[72px]" : "w-60"
      )}
    >
      {/* Logo */}
      <div className="p-4 border-b border-sidebar-border">
        <Link href="/dashboard" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shrink-0">
            <span className="text-primary-foreground font-bold text-sm">R</span>
          </div>
          {!sidebarCollapsed && (
            <div className="flex items-baseline">
              <span className="font-sans font-extrabold text-foreground">Rescue</span>
              <span className="font-sans font-extrabold text-primary">AI</span>
            </div>
          )}
        </Link>
      </div>

      {/* Theme Toggle */}
      {!sidebarCollapsed && (
        <div className="px-4 py-3 border-b border-sidebar-border">
          <div className="flex items-center bg-muted rounded-lg p-1">
            <button
              onClick={() => setTheme('light')}
              className={cn(
                "flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-md text-xs font-mono transition-colors",
                theme === 'light' ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Sun className="w-3.5 h-3.5" />
              Light
            </button>
            <button
              onClick={() => setTheme('dark')}
              className={cn(
                "flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-md text-xs font-mono transition-colors",
                theme === 'dark' ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Moon className="w-3.5 h-3.5" />
              Dark
            </button>
          </div>
        </div>
      )}

      {/* Weather Selector */}
      {!sidebarCollapsed && currentUser.role === 'volunteer' && (
        <div className="px-4 py-3 border-b border-sidebar-border">
          <label className="text-[10px] font-mono text-muted-foreground uppercase tracking-wide block mb-2">
            Weather Condition
          </label>
          <select
            value={weatherCondition}
            onChange={(e) => setWeatherCondition(e.target.value as WeatherCondition)}
            className="w-full h-9 px-3 rounded-lg border border-input bg-background text-sm font-mono focus:outline-none focus:ring-2 focus:ring-ring"
          >
            {weatherConditions.map((condition) => (
              <option key={condition} value={condition}>
                {weatherLabels[condition]}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Live Stats */}
      {!sidebarCollapsed && currentUser.role === 'volunteer' && (
        <div className="px-4 py-3 border-b border-sidebar-border">
          <div className="grid grid-cols-2 gap-2">
            <MiniStatCard label="Active" value={activeCases} color="red" />
            <MiniStatCard label="Online" value={onlineVolunteers} color="green" />
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 p-2 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          const Icon = item.icon
          
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 transition-colors relative",
                isActive 
                  ? "bg-sidebar-accent text-sidebar-primary" 
                  : "text-sidebar-foreground hover:bg-sidebar-accent/50",
                sidebarCollapsed && "justify-center"
              )}
            >
              {isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-sidebar-primary rounded-r" />
              )}
              <Icon className={cn("w-5 h-5 shrink-0", isActive && "text-sidebar-primary")} />
              {!sidebarCollapsed && (
                <span className="text-sm font-medium">{item.label}</span>
              )}
            </Link>
          )
        })}
      </nav>

      {/* User Section */}
      <div className="p-4 border-t border-sidebar-border">
        {!sidebarCollapsed ? (
          <div className="flex items-center gap-3">
            <UserAvatar name={currentUser.name} role={currentUser.role} size="md" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-sidebar-foreground truncate">{currentUser.name}</p>
              <p className="text-[10px] font-mono text-muted-foreground uppercase">{currentUser.role}</p>
            </div>
            <Button variant="ghost" size="icon" className="shrink-0" onClick={handleLogout}>
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <UserAvatar name={currentUser.name} role={currentUser.role} size="sm" />
            <Button variant="ghost" size="icon" className="w-8 h-8" onClick={handleLogout}>
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        )}
      </div>

      {/* Collapse Toggle */}
      <button
        onClick={toggleSidebar}
        className="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-card border border-border flex items-center justify-center hover:bg-muted transition-colors"
      >
        {sidebarCollapsed ? (
          <ChevronRight className="w-3.5 h-3.5" />
        ) : (
          <ChevronLeft className="w-3.5 h-3.5" />
        )}
      </button>
    </aside>
  )
}
