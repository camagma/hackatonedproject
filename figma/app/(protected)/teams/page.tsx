'use client'

import { useAppStore } from "@/lib/store"
import { PageHeader, SectionHeader, PriorityBadge, VolunteerAvatar, OnlineBadge, CaseIdBadge } from "@/components/rescue"
import { Button } from "@/components/ui/button"
import { ChevronDown, ChevronUp, MapPin, Cloud, ExternalLink, RefreshCw, X } from "lucide-react"
import { useState } from "react"

export default function TeamsPage() {
  const { cases, volunteers, teams, weatherCondition } = useAppStore()
  const [expandedCases, setExpandedCases] = useState<string[]>([])

  const activeCases = cases.filter(c => c.status === 'active' || c.status === 'assigned')
  const onlineVolunteers = volunteers.filter(v => v.status === 'active')
  const eligibleVolunteers = onlineVolunteers.filter(v => !v.skills || v.skills.length > 0)

  const toggleCase = (caseId: string) => {
    setExpandedCases(prev => 
      prev.includes(caseId) 
        ? prev.filter(id => id !== caseId)
        : [...prev, caseId]
    )
  }

  const getCaseTeam = (caseId: string) => teams.find(t => t.caseId === caseId)

  const getWeatherDelta = () => {
    const deltas: Record<string, number> = {
      clear: 0,
      rain: 10,
      storm: 20,
      snow: 15,
      fog: 10,
      extreme_heat: 15,
    }
    return deltas[weatherCondition] || 0
  }

  return (
    <div className="p-6">
      <PageHeader title="Teams Management" showTimestamp />

      {/* Summary Strip */}
      <div className="mt-6 bg-card rounded-xl border p-4 flex items-center gap-6 text-xs font-mono">
        <div>
          <span className="text-muted-foreground">Active Cases: </span>
          <span className="text-critical font-semibold">{activeCases.length}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Online Free: </span>
          <span className="text-online font-semibold">{onlineVolunteers.length}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Eligible Free: </span>
          <span className="text-info font-semibold">{eligibleVolunteers.length}</span>
        </div>
        <div className="ml-auto text-muted-foreground">
          Functions: <code className="bg-muted px-1 rounded">buildTeam()</code> <code className="bg-muted px-1 rounded">releaseTeam()</code>
        </div>
      </div>

      {/* Cases with Team Info */}
      <div className="mt-6 space-y-4">
        {activeCases.length === 0 ? (
          <div className="bg-card rounded-xl border p-8 text-center">
            <p className="text-muted-foreground font-mono text-sm">No active cases requiring teams</p>
          </div>
        ) : (
          activeCases.map(caseData => {
            const team = getCaseTeam(caseData.id)
            const isExpanded = expandedCases.includes(caseData.id)
            const weatherDelta = getWeatherDelta()
            const effectiveScore = caseData.priorityScore + weatherDelta + (caseData.aiAnalysis?.timeModifier || 0)

            return (
              <div key={caseData.id} className="bg-card rounded-xl border overflow-hidden">
                {/* Header */}
                <button
                  onClick={() => toggleCase(caseData.id)}
                  className="w-full p-4 flex items-center gap-4 text-left hover:bg-muted/50 transition-colors"
                >
                  <CaseIdBadge caseId={caseData.id} />
                  <span className="font-sans font-bold text-foreground">{caseData.name}</span>
                  <span className="text-xs font-mono text-muted-foreground">{caseData.emergencyType}</span>
                  <div className="ml-auto flex items-center gap-3">
                    <PriorityBadge priority={caseData.priority} score={effectiveScore} />
                    {team && (
                      <span className="text-xs font-mono text-info">
                        Team: {team.name}
                      </span>
                    )}
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </div>
                </button>

                {/* Expanded Content */}
                {isExpanded && (
                  <div className="p-4 border-t border-border space-y-4">
                    {/* Badges Row */}
                    <div className="flex items-center gap-3 flex-wrap">
                      <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-muted text-xs font-mono">
                        Effective: <span className="text-primary font-semibold">{effectiveScore}</span>
                      </div>
                      {team && (
                        <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-info-dim text-info text-xs font-mono">
                          {team.type}
                        </div>
                      )}
                      <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-muted text-xs font-mono text-muted-foreground">
                        <MapPin className="w-3 h-3" />
                        {caseData.lastKnownAddress}
                      </div>
                      {weatherDelta > 0 && (
                        <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-high-dim text-high text-xs font-mono">
                          <Cloud className="w-3 h-3" />
                          Weather +{weatherDelta}
                        </div>
                      )}
                    </div>

                    {/* Required Roles */}
                    {caseData.aiAnalysis?.skills && (
                      <div>
                        <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-wide mb-2">
                          Required Roles
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {caseData.aiAnalysis.skills.map((skill, i) => (
                            <span key={i} className="px-2 py-0.5 rounded bg-secondary text-secondary-foreground text-xs font-mono">
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Two Columns: Current Team | Recommended */}
                    <div className="grid grid-cols-2 gap-4">
                      {/* Current Team */}
                      <div>
                        <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-wide mb-2">
                          Current Team
                        </p>
                        {team ? (
                          <div className="space-y-2">
                            {team.members.map(memberId => {
                              const member = volunteers.find(v => v.id === memberId)
                              if (!member) return null
                              return (
                                <div key={memberId} className="flex items-center gap-2 p-2 rounded-lg bg-muted">
                                  <VolunteerAvatar name={member.name} status={member.status} size="sm" />
                                  <div className="flex-1 min-w-0">
                                    <p className="text-xs font-medium truncate">{member.name}</p>
                                    <p className="text-[10px] font-mono text-muted-foreground">
                                      {member.skills?.join(', ')}
                                    </p>
                                  </div>
                                  <OnlineBadge status={member.status || 'unknown'} />
                                </div>
                              )
                            })}
                          </div>
                        ) : (
                          <p className="text-xs font-mono text-muted-foreground">No team assigned</p>
                        )}
                      </div>

                      {/* Recommended Team */}
                      <div>
                        <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-wide mb-2">
                          Recommended Team
                        </p>
                        <div className="space-y-2">
                          {eligibleVolunteers.slice(0, 3).map(volunteer => (
                            <div key={volunteer.id} className="flex items-center gap-2 p-2 rounded-lg bg-muted">
                              <VolunteerAvatar name={volunteer.name} status={volunteer.status} size="sm" />
                              <div className="flex-1 min-w-0">
                                <p className="text-xs font-medium truncate">{volunteer.name}</p>
                                <p className="text-[10px] font-mono text-muted-foreground">
                                  {volunteer.skills?.join(', ')}
                                </p>
                              </div>
                              <span className="text-[10px] font-mono text-muted-foreground">
                                2.3 km
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center gap-2 pt-2 border-t border-border">
                      <Button size="sm" className="gap-1.5">
                        <RefreshCw className="w-3.5 h-3.5" />
                        {team ? 'Rebuild Team' : 'Create Team'}
                      </Button>
                      {team && (
                        <Button size="sm" variant="outline" className="gap-1.5">
                          <X className="w-3.5 h-3.5" />
                          Release Team
                        </Button>
                      )}
                      <Button size="sm" variant="ghost" className="gap-1.5 ml-auto">
                        <ExternalLink className="w-3.5 h-3.5" />
                        Open Case
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
