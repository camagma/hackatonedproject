'use client'

import { useState } from 'react'
import { cn } from "@/lib/utils"
import { PriorityBadge, OnlineBadge, CaseIdBadge, StatusBadge } from "./badges"
import { VolunteerAvatar } from "./avatars"
import { Button } from "@/components/ui/button"
import { ChevronDown, ChevronUp, User, Users, Plus, Check, MapPin, Clock, Tag, AlertTriangle } from "lucide-react"
import type { Case, User as UserType } from "@/lib/store"

interface CaseCardProps {
  caseData: Case
  volunteers?: UserType[]
  isReporterView?: boolean
  onFound?: (caseId: string) => void
  onAssignAI?: (caseId: string) => void
  onSmartTeam?: (caseId: string) => void
  onJoinTeam?: (caseId: string) => void
  onCloseSearch?: (caseId: string, note?: string) => void
  className?: string
}

export function CaseCard({
  caseData,
  volunteers = [],
  isReporterView = false,
  onFound,
  onAssignAI,
  onSmartTeam,
  onJoinTeam,
  onCloseSearch,
  className,
}: CaseCardProps) {
  const [expanded, setExpanded] = useState(false)
  const [closeNote, setCloseNote] = useState('')

  const borderColors = {
    critical: 'border-l-critical',
    high: 'border-l-high',
    medium: 'border-l-medium',
    low: 'border-l-low',
  }

  const getTimeAgo = (date: Date) => {
    const hours = Math.floor((Date.now() - new Date(date).getTime()) / 3600000)
    if (hours < 1) return 'Just now'
    if (hours === 1) return '1 hour ago'
    return `${hours} hours ago`
  }

  const assignedVolunteer = volunteers.find(v => v.id === caseData.assignedVolunteerId)

  return (
    <div
      className={cn(
        "bg-card rounded-xl border border-l-4 p-4 transition-all hover:translate-y-[-1px] hover:border-border/80",
        borderColors[caseData.priority],
        className
      )}
    >
      <div className="flex gap-4">
        {/* Photo/Placeholder */}
        <div className="shrink-0">
          {caseData.photo ? (
            <img
              src={caseData.photo}
              alt={caseData.name}
              className="w-[78px] h-[78px] rounded-[18px] object-cover"
            />
          ) : (
            <div className="w-[78px] h-[78px] rounded-[18px] bg-muted flex items-center justify-center">
              <User className="w-8 h-8 text-muted-foreground" />
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Header row */}
          <div className="flex items-start justify-between gap-2 mb-2">
            <div>
              <h3 className="font-sans font-bold text-foreground">
                {caseData.name}, {caseData.age}
              </h3>
              <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono mt-0.5 flex-wrap">
                <span className="flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  {caseData.lastKnownAddress}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {getTimeAgo(caseData.createdAt)}
                </span>
                <span className="flex items-center gap-1">
                  <Tag className="w-3 h-3" />
                  {caseData.emergencyType}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <PriorityBadge priority={caseData.priority} score={caseData.priorityScore} />
              {caseData.aiAnalysis && caseData.aiAnalysis.weatherModifier + caseData.aiAnalysis.timeModifier > 0 && (
                <span className="text-xs font-mono text-high">
                  +{caseData.aiAnalysis.weatherModifier + caseData.aiAnalysis.timeModifier}
                </span>
              )}
            </div>
          </div>

          {/* Description */}
          <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
            {caseData.description}
          </p>

          {/* Bottom row */}
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 flex-wrap">
              {assignedVolunteer && (
                <div className="flex items-center gap-1.5">
                  <VolunteerAvatar name={assignedVolunteer.name} status={assignedVolunteer.status} size="sm" />
                  <span className="text-xs font-mono text-muted-foreground">{assignedVolunteer.name}</span>
                </div>
              )}
              <StatusBadge status="neutral">{caseData.status.toUpperCase()}</StatusBadge>
              <CaseIdBadge caseId={caseData.id} />
            </div>
          </div>
        </div>
      </div>

      {/* Volunteer Actions */}
      {!isReporterView && (
        <div className="flex items-center gap-2 mt-4 pt-4 border-t border-border">
          <Button size="sm" variant="outline" className="gap-1.5" onClick={() => onFound?.(caseData.id)}>
            <Check className="w-3.5 h-3.5" />
            Found
          </Button>
          <Button size="sm" variant="outline" className="gap-1.5" onClick={() => onAssignAI?.(caseData.id)}>
            <User className="w-3.5 h-3.5" />
            Assign AI
          </Button>
          <Button size="sm" variant="outline" className="gap-1.5" onClick={() => onSmartTeam?.(caseData.id)}>
            <Users className="w-3.5 h-3.5" />
            Smart Team
          </Button>
          <Button size="sm" variant="outline" className="gap-1.5" onClick={() => onJoinTeam?.(caseData.id)}>
            <Plus className="w-3.5 h-3.5" />
            Join Team
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="ml-auto gap-1"
            onClick={() => setExpanded(!expanded)}
          >
            AI Analysis
            {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </Button>
        </div>
      )}

      {/* Reporter Actions */}
      {isReporterView && caseData.status === 'active' && (
        <div className="flex items-center gap-2 mt-4 pt-4 border-t border-border">
          <input
            type="text"
            placeholder="Optional note..."
            value={closeNote}
            onChange={(e) => setCloseNote(e.target.value)}
            className="flex-1 h-8 px-3 rounded-lg border border-input bg-background text-sm font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <Button
            size="sm"
            className="gap-1.5 bg-online text-white hover:bg-online/90"
            onClick={() => onCloseSearch?.(caseData.id, closeNote)}
          >
            <Check className="w-3.5 h-3.5" />
            Close search
          </Button>
        </div>
      )}

      {/* AI Analysis Expansion */}
      {expanded && caseData.aiAnalysis && (
        <div className="mt-4 pt-4 border-t border-border space-y-3">
          <div>
            <h4 className="text-xs font-mono font-semibold text-muted-foreground uppercase mb-1">Reasoning</h4>
            <p className="text-sm text-foreground">{caseData.aiAnalysis.reasoning}</p>
          </div>
          
          <div>
            <h4 className="text-xs font-mono font-semibold text-muted-foreground uppercase mb-1">Risk Factors</h4>
            <div className="flex flex-wrap gap-1.5">
              {caseData.aiAnalysis.riskFactors.map((factor, i) => (
                <span key={i} className="px-2 py-0.5 rounded bg-critical-dim text-critical text-xs font-mono">
                  {factor}
                </span>
              ))}
            </div>
          </div>

          <div>
            <h4 className="text-xs font-mono font-semibold text-muted-foreground uppercase mb-1">Required Skills</h4>
            <div className="flex flex-wrap gap-1.5">
              {caseData.aiAnalysis.skills.map((skill, i) => (
                <span key={i} className="px-2 py-0.5 rounded bg-info-dim text-info text-xs font-mono">
                  {skill}
                </span>
              ))}
            </div>
          </div>

          <div>
            <h4 className="text-xs font-mono font-semibold text-muted-foreground uppercase mb-1">Recommended Action</h4>
            <p className="text-sm text-foreground">{caseData.aiAnalysis.recommendedAction}</p>
          </div>

          {(caseData.aiAnalysis.weatherModifier > 0 || caseData.aiAnalysis.timeModifier > 0) && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-high-dim border border-high/30">
              <AlertTriangle className="w-4 h-4 text-high shrink-0" />
              <div className="text-xs font-mono">
                <span className="text-high font-semibold">DYNAMIC RISK:</span>
                <span className="text-foreground ml-2">
                  Weather +{caseData.aiAnalysis.weatherModifier} | Time +{caseData.aiAnalysis.timeModifier} = 
                  <span className="text-high font-semibold ml-1">Effective Score {caseData.aiAnalysis.effectiveScore}</span>
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
