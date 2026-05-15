'use client'

import { useAppStore } from "@/lib/store"
import { PageHeader, SectionHeader, CaseCard } from "@/components/rescue"

export default function MyReportsPage() {
  const { currentUser, cases, volunteers, updateCase } = useAppStore()
  
  if (!currentUser) return null

  const myReports = cases.filter(c => c.reporterId === currentUser.id)
  const activeReports = myReports.filter(c => c.status === 'active' || c.status === 'assigned')
  const resolvedReports = myReports.filter(c => c.status === 'found' || c.status === 'closed')

  const handleCloseSearch = (caseId: string, note?: string) => {
    updateCase(caseId, {
      status: 'found',
    })
  }

  return (
    <div className="p-6">
      <PageHeader title="My Reports" showTimestamp />

      {/* Active Reports */}
      <div className="mt-6">
        <div className="flex items-center gap-4 mb-4">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-critical" />
            <h2 className="text-sm font-sans font-bold text-foreground uppercase tracking-wide">
              Active ({activeReports.length})
            </h2>
          </div>
          <div className="flex-1 h-px bg-border" />
        </div>
        <div className="space-y-4">
          {activeReports.length === 0 ? (
            <div className="bg-card rounded-xl border p-8 text-center">
              <p className="text-muted-foreground font-mono text-sm">No active reports</p>
            </div>
          ) : (
            activeReports.map(caseData => (
              <CaseCard
                key={caseData.id}
                caseData={caseData}
                volunteers={volunteers}
                isReporterView
                onCloseSearch={handleCloseSearch}
              />
            ))
          )}
        </div>
      </div>

      {/* Resolved Reports */}
      <div className="mt-8">
        <div className="flex items-center gap-4 mb-4">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-online" />
            <h2 className="text-sm font-sans font-bold text-foreground uppercase tracking-wide">
              Resolved ({resolvedReports.length})
            </h2>
          </div>
          <div className="flex-1 h-px bg-border" />
        </div>
        <div className="space-y-4">
          {resolvedReports.length === 0 ? (
            <div className="bg-card rounded-xl border p-8 text-center">
              <p className="text-muted-foreground font-mono text-sm">No resolved reports yet</p>
            </div>
          ) : (
            resolvedReports.map(caseData => (
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
    </div>
  )
}
