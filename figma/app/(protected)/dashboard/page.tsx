'use client'

import { useAppStore } from "@/lib/store"
import { PageHeader, SectionHeader, StatCard, CaseCard, VolunteerAvatar, OnlineBadge } from "@/components/rescue"
import { Button } from "@/components/ui/button"
import { Users, Plus, AlertTriangle } from "lucide-react"

export default function DashboardPage() {
  const { currentUser, cases, volunteers, weatherCondition } = useAppStore()
  
  if (!currentUser) return null

  const isVolunteer = currentUser.role === 'volunteer'
  
  // Stats
  const activeCases = cases.filter(c => c.status === 'active' || c.status === 'assigned')
  const criticalCases = cases.filter(c => c.priority === 'critical' && c.status !== 'found' && c.status !== 'closed')
  const onlineVolunteers = volunteers.filter(v => v.status === 'active')
  const foundCases = cases.filter(c => c.status === 'found')

  // Get highest priority cases
  const priorityCases = [...activeCases]
    .sort((a, b) => b.priorityScore - a.priorityScore)
    .slice(0, 5)

  // Check if risk conditions exist
  const isNightHours = () => {
    const hour = new Date().getHours()
    return hour < 6 || hour > 20
  }
  const hasRiskConditions = weatherCondition !== 'clear' || isNightHours()

  if (!isVolunteer) {
    // Reporter Dashboard
    const myReports = cases.filter(c => c.reporterId === currentUser.id)
    const myActiveReports = myReports.filter(c => c.status === 'active' || c.status === 'assigned')
    const myFoundReports = myReports.filter(c => c.status === 'found')

    return (
      <div className="p-6">
        <PageHeader title="My Overview" showTimestamp>
          <span className="px-3 py-1 rounded-full bg-info-dim text-info text-xs font-mono uppercase">
            Reporter
          </span>
        </PageHeader>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mt-6">
          <StatCard label="Active Reports" value={myActiveReports.length} color="red" />
          <StatCard label="Found" value={myFoundReports.length} color="green" />
          <StatCard label="Total Reports" value={myReports.length} color="blue" />
        </div>

        {/* Active Reports */}
        <div className="mt-8">
          <SectionHeader label="Active Reports" />
          <div className="space-y-4">
            {myActiveReports.length === 0 ? (
              <div className="bg-card rounded-xl border p-8 text-center">
                <p className="text-muted-foreground font-mono text-sm">No active reports</p>
              </div>
            ) : (
              myActiveReports.map(caseData => (
                <CaseCard
                  key={caseData.id}
                  caseData={caseData}
                  volunteers={volunteers}
                  isReporterView
                />
              ))
            )}
          </div>
        </div>

        {/* System Status */}
        <details className="mt-8 bg-card rounded-xl border p-4">
          <summary className="cursor-pointer text-sm font-sans font-bold text-foreground">
            System Status
          </summary>
          <div className="mt-4 font-mono text-xs text-muted-foreground space-y-1">
            <p>Online Volunteers: <span className="text-online">{onlineVolunteers.length}</span></p>
            <p>Total Volunteers: {volunteers.length}</p>
            <p>Active Cases System-wide: {activeCases.length}</p>
          </div>
        </details>
      </div>
    )
  }

  // Volunteer Dashboard
  return (
    <div className="p-6">
      <PageHeader title="Operations Dashboard" showTimestamp />

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-4 mt-6">
        <StatCard 
          label="Active Cases" 
          value={activeCases.length} 
          subtitle="Requiring attention"
          color="red" 
        />
        <StatCard 
          label="Critical" 
          value={criticalCases.length} 
          subtitle="High priority"
          color="orange" 
        />
        <StatCard 
          label="Online Now" 
          value={onlineVolunteers.length} 
          subtitle="Available volunteers"
          color="green" 
        />
        <StatCard 
          label="Found Total" 
          value={foundCases.length} 
          subtitle="Successfully resolved"
          color="blue" 
        />
      </div>

      {/* Dynamic Risk Banner */}
      {hasRiskConditions && (
        <div className="mt-6 p-4 rounded-xl bg-high-dim border border-high/30 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-high shrink-0" />
          <div>
            <p className="text-sm font-sans font-bold text-foreground">Elevated Risk Conditions</p>
            <p className="text-xs font-mono text-muted-foreground">
              {weatherCondition !== 'clear' && `Weather: ${weatherCondition.replace('_', ' ')}`}
              {weatherCondition !== 'clear' && isNightHours() && ' | '}
              {isNightHours() && 'Night hours active'}
              {' - Priority scores may be adjusted'}
            </p>
          </div>
        </div>
      )}

      {/* Team Action Row */}
      <div className="mt-6 flex items-center gap-4">
        <Button variant="outline" className="gap-2">
          <Users className="w-4 h-4" />
          Team Builder
        </Button>
        <Button variant="outline" className="gap-2">
          <Plus className="w-4 h-4" />
          Create Team
        </Button>
        <span className="text-xs font-mono text-muted-foreground">
          {onlineVolunteers.length} volunteers available for assignment
        </span>
      </div>

      {/* Main Content Split */}
      <div className="mt-6 grid grid-cols-5 gap-6">
        {/* Left: Priority Cases (3 cols) */}
        <div className="col-span-3">
          <SectionHeader label="Highest Priority Cases" />
          <div className="space-y-4">
            {priorityCases.length === 0 ? (
              <div className="bg-card rounded-xl border p-8 text-center">
                <p className="text-muted-foreground font-mono text-sm">No active cases</p>
              </div>
            ) : (
              priorityCases.map(caseData => (
                <CaseCard
                  key={caseData.id}
                  caseData={caseData}
                  volunteers={volunteers}
                />
              ))
            )}
          </div>
        </div>

        {/* Right: Team Status (2 cols) */}
        <div className="col-span-2">
          <SectionHeader label="Team Status" />
          <div className="space-y-3">
            {volunteers.map(volunteer => (
              <div
                key={volunteer.id}
                className="bg-card rounded-xl border p-4 flex items-center gap-3"
              >
                <VolunteerAvatar name={volunteer.name} status={volunteer.status} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">{volunteer.name}</p>
                  <p className="text-xs font-mono text-muted-foreground">
                    {volunteer.skills?.join(', ') || 'No skills listed'}
                  </p>
                </div>
                <OnlineBadge status={volunteer.status || 'unknown'} lastPing={volunteer.lastPing} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
