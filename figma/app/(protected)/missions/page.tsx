'use client'

import { useAppStore } from "@/lib/store"
import { PageHeader, CaseCard, SectionHeader } from "@/components/rescue"

export default function MissionsPage() {
  const { currentUser, cases, volunteers } = useAppStore()
  
  if (!currentUser) return null

  const assignedCases = cases.filter(c => c.assignedVolunteerId === currentUser.id)
  const activeMissions = assignedCases.filter(c => c.status === 'active' || c.status === 'assigned')
  const completedMissions = assignedCases.filter(c => c.status === 'found' || c.status === 'closed')

  return (
    <div className="p-6">
      <PageHeader title="My Missions" showTimestamp />

      {/* Active Missions */}
      <div className="mt-6">
        <SectionHeader label={`Active Missions (${activeMissions.length})`} />
        <div className="space-y-4">
          {activeMissions.length === 0 ? (
            <div className="bg-card rounded-xl border p-8 text-center">
              <p className="text-muted-foreground font-mono text-sm">No active missions assigned to you</p>
            </div>
          ) : (
            activeMissions.map(caseData => (
              <CaseCard
                key={caseData.id}
                caseData={caseData}
                volunteers={volunteers}
              />
            ))
          )}
        </div>
      </div>

      {/* Completed Missions */}
      <div className="mt-8">
        <SectionHeader label={`Completed Missions (${completedMissions.length})`} />
        <div className="space-y-4">
          {completedMissions.length === 0 ? (
            <div className="bg-card rounded-xl border p-8 text-center">
              <p className="text-muted-foreground font-mono text-sm">No completed missions yet</p>
            </div>
          ) : (
            completedMissions.map(caseData => (
              <CaseCard
                key={caseData.id}
                caseData={caseData}
                volunteers={volunteers}
              />
            ))
          )}
        </div>
      </div>
    </div>
  )
}
