'use client'

import { useState } from 'react'
import { useAppStore, type CaseStatus } from "@/lib/store"
import { PageHeader, CaseCard } from "@/components/rescue"

const statusOptions: { value: CaseStatus | 'all'; label: string }[] = [
  { value: 'all', label: 'All Status' },
  { value: 'active', label: 'Active' },
  { value: 'assigned', label: 'Assigned' },
  { value: 'found', label: 'Found' },
  { value: 'closed', label: 'Closed' },
]

const categoryOptions = [
  { value: 'all', label: 'All Categories' },
  { value: 'Missing Person', label: 'Missing Person' },
  { value: 'Lost Hiker', label: 'Lost Hiker' },
  { value: 'Vehicle Breakdown', label: 'Vehicle Breakdown' },
]

export default function CasesPage() {
  const { cases, volunteers } = useAppStore()
  
  const [statusFilter, setStatusFilter] = useState<CaseStatus | 'all'>('all')
  const [categoryFilter, setCategoryFilter] = useState('all')

  const filteredCases = cases.filter(c => {
    if (statusFilter !== 'all' && c.status !== statusFilter) return false
    if (categoryFilter !== 'all' && c.emergencyType !== categoryFilter) return false
    return true
  }).sort((a, b) => b.priorityScore - a.priorityScore)

  return (
    <div className="p-6">
      <PageHeader title="All Cases" showTimestamp />

      {/* Filter Row */}
      <div className="mt-6 flex items-center gap-4">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as CaseStatus | 'all')}
          className="h-10 px-3 rounded-[14px] border border-input bg-background text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary"
        >
          {statusOptions.map(option => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="h-10 px-3 rounded-[14px] border border-input bg-background text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary"
        >
          {categoryOptions.map(option => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>

        <span className="text-xs font-mono text-muted-foreground ml-auto">
          {filteredCases.length} case{filteredCases.length !== 1 ? 's' : ''} found
        </span>
      </div>

      {/* Case List */}
      <div className="mt-6 space-y-4">
        {filteredCases.length === 0 ? (
          <div className="bg-card rounded-xl border p-8 text-center">
            <p className="text-muted-foreground font-mono text-sm">No cases match the selected filters</p>
          </div>
        ) : (
          filteredCases.map(caseData => (
            <CaseCard
              key={caseData.id}
              caseData={caseData}
              volunteers={volunteers}
            />
          ))
        )}
      </div>
    </div>
  )
}
