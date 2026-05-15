'use client'

import { useState, useRef } from 'react'
import { useAppStore, type Priority } from "@/lib/store"
import { PageHeader, SectionHeader, PriorityBadge } from "@/components/rescue"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Bot, Upload, X, User } from "lucide-react"

const ageGroupOptions = [
  { value: 'child', label: 'Child (0-12)' },
  { value: 'teen', label: 'Teen (13-17)' },
  { value: 'adult', label: 'Adult (18-64)' },
  { value: 'elderly', label: 'Elderly (65+)' },
]

const emergencyTypeOptions = [
  { value: 'Missing Person', label: 'Missing Person' },
  { value: 'Lost Hiker', label: 'Lost Hiker' },
  { value: 'Vehicle Breakdown', label: 'Vehicle Breakdown' },
  { value: 'Medical Emergency', label: 'Medical Emergency' },
  { value: 'Natural Disaster', label: 'Natural Disaster' },
  { value: 'Other', label: 'Other' },
]

export default function ReportPage() {
  const { currentUser, addCase, addAILogEntry, teams } = useAppStore()
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const [fullName, setFullName] = useState('')
  const [age, setAge] = useState('')
  const [ageGroup, setAgeGroup] = useState('adult')
  const [emergencyType, setEmergencyType] = useState('Missing Person')
  const [photo, setPhoto] = useState<string | null>(null)
  const [address, setAddress] = useState('')
  const [hoursMissing, setHoursMissing] = useState('')
  const [phone, setPhone] = useState('')
  const [circumstances, setCircumstances] = useState('')
  
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [result, setResult] = useState<{
    priority: Priority
    score: number
    reasoning: string
    assignedTeam?: string
  } | null>(null)

  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onloadend = () => {
        setPhoto(reader.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  const calculatePriority = (): { priority: Priority; score: number; reasoning: string } => {
    let score = 50
    const factors: string[] = []

    // Age factors
    const ageNum = parseInt(age)
    if (ageNum < 12) {
      score += 30
      factors.push(`Young age (${ageNum}) significantly increases risk`)
    } else if (ageNum > 65) {
      score += 20
      factors.push(`Elderly age (${ageNum}) increases vulnerability`)
    }

    // Time missing
    const hours = parseInt(hoursMissing) || 0
    if (hours > 24) {
      score += 20
      factors.push(`Extended time missing (${hours}h) raises concern`)
    } else if (hours > 8) {
      score += 10
      factors.push(`Moderate time elapsed (${hours}h)`)
    }

    // Emergency type
    if (emergencyType === 'Medical Emergency') {
      score += 15
      factors.push('Medical emergency requires immediate response')
    } else if (emergencyType === 'Natural Disaster') {
      score += 15
      factors.push('Natural disaster conditions present additional hazards')
    }

    // Cap score
    score = Math.min(100, score)

    const priority: Priority = 
      score >= 80 ? 'critical' :
      score >= 60 ? 'high' :
      score >= 40 ? 'medium' : 'low'

    return {
      priority,
      score,
      reasoning: factors.length > 0 
        ? factors.join('. ') + '.'
        : 'Standard priority based on reported circumstances.',
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!currentUser) return

    setIsSubmitting(true)
    
    // Simulate AI processing
    await new Promise(resolve => setTimeout(resolve, 1500))

    const { priority, score, reasoning } = calculatePriority()
    
    // Create the case
    addCase({
      name: fullName,
      age: parseInt(age),
      ageGroup,
      emergencyType,
      description: circumstances,
      lastKnownAddress: address,
      hoursMissing: parseInt(hoursMissing) || 0,
      phone,
      photo: photo || undefined,
      priority,
      priorityScore: score,
      status: 'active',
      reporterId: currentUser.id,
      aiAnalysis: {
        reasoning,
        riskFactors: [],
        skills: ['First Aid', 'Navigation'],
        recommendedAction: 'Deploy search team to last known location.',
        weatherModifier: 0,
        timeModifier: 0,
        effectiveScore: score,
      },
    })

    // Log AI activity
    addAILogEntry({
      priority,
      eventTitle: 'New Case Analyzed',
      detail: `Case for ${fullName} assigned ${priority.toUpperCase()} priority (score: ${score}). ${reasoning}`,
    })

    setResult({
      priority,
      score,
      reasoning,
      assignedTeam: teams[0]?.name,
    })

    setIsSubmitting(false)
  }

  const resetForm = () => {
    setFullName('')
    setAge('')
    setAgeGroup('adult')
    setEmergencyType('Missing Person')
    setPhoto(null)
    setAddress('')
    setHoursMissing('')
    setPhone('')
    setCircumstances('')
    setResult(null)
  }

  return (
    <div className="p-6">
      <PageHeader title="Report Missing Person" showTimestamp />

      {!result ? (
        <form onSubmit={handleSubmit} className="mt-6 bg-card rounded-[20px] border p-6">
          <div className="grid grid-cols-2 gap-6">
            {/* Left Column */}
            <div className="space-y-4">
              <div className="space-y-2">
                <Label className="text-xs font-mono uppercase tracking-wide">Full Name</Label>
                <Input
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Enter full name"
                  className="h-11 rounded-[14px] font-mono"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-xs font-mono uppercase tracking-wide">Age</Label>
                  <Input
                    type="number"
                    value={age}
                    onChange={(e) => setAge(e.target.value)}
                    placeholder="Age"
                    min="0"
                    max="120"
                    className="h-11 rounded-[14px] font-mono"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs font-mono uppercase tracking-wide">Age Group</Label>
                  <select
                    value={ageGroup}
                    onChange={(e) => setAgeGroup(e.target.value)}
                    className="w-full h-11 px-3 rounded-[14px] border border-input bg-background text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    {ageGroupOptions.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-xs font-mono uppercase tracking-wide">Emergency Type</Label>
                <select
                  value={emergencyType}
                  onChange={(e) => setEmergencyType(e.target.value)}
                  className="w-full h-11 px-3 rounded-[14px] border border-input bg-background text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  {emergencyTypeOptions.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <Label className="text-xs font-mono uppercase tracking-wide">Photo (Optional)</Label>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handlePhotoUpload}
                  className="hidden"
                />
                {photo ? (
                  <div className="relative w-32 h-32">
                    <img src={photo} alt="Uploaded" className="w-full h-full object-cover rounded-xl" />
                    <button
                      type="button"
                      onClick={() => setPhoto(null)}
                      className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-destructive text-white flex items-center justify-center"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="w-32 h-32 rounded-xl border-2 border-dashed border-border flex flex-col items-center justify-center gap-2 hover:border-primary transition-colors"
                  >
                    <Upload className="w-6 h-6 text-muted-foreground" />
                    <span className="text-xs font-mono text-muted-foreground">Upload</span>
                  </button>
                )}
              </div>
            </div>

            {/* Right Column */}
            <div className="space-y-4">
              <div className="space-y-2">
                <Label className="text-xs font-mono uppercase tracking-wide">Last Known Address</Label>
                <Input
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="Enter last known location"
                  className="h-11 rounded-[14px] font-mono"
                  required
                />
                <p className="text-[10px] font-mono text-muted-foreground">
                  Be as specific as possible (street, landmarks, etc.)
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-xs font-mono uppercase tracking-wide">Hours Missing</Label>
                  <Input
                    type="number"
                    value={hoursMissing}
                    onChange={(e) => setHoursMissing(e.target.value)}
                    placeholder="Hours"
                    min="0"
                    className="h-11 rounded-[14px] font-mono"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs font-mono uppercase tracking-wide">Contact Phone</Label>
                  <Input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="Phone number"
                    className="h-11 rounded-[14px] font-mono"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Full Width Circumstances */}
          <div className="mt-6 space-y-2">
            <Label className="text-xs font-mono uppercase tracking-wide">Circumstances</Label>
            <Textarea
              value={circumstances}
              onChange={(e) => setCircumstances(e.target.value)}
              placeholder="Describe the circumstances of the disappearance, what they were wearing, any relevant medical conditions, etc."
              className="rounded-[14px] font-mono min-h-[120px]"
              required
            />
          </div>

          {/* Submit Button */}
          <Button 
            type="submit" 
            className="w-full mt-6 h-12 rounded-[14px] font-sans font-bold gap-2"
            disabled={isSubmitting}
          >
            <Bot className="w-5 h-5" />
            {isSubmitting ? 'Analyzing...' : 'Submit & Run AI Analysis'}
          </Button>
        </form>
      ) : (
        /* Result Panel */
        <div className="mt-6 bg-card rounded-[20px] border p-6">
          <div className="text-center mb-6">
            <div className="w-16 h-16 rounded-full bg-online-dim flex items-center justify-center mx-auto mb-4">
              <User className="w-8 h-8 text-online" />
            </div>
            <h2 className="text-xl font-sans font-bold text-foreground">Report Submitted Successfully</h2>
            <p className="text-sm text-muted-foreground mt-1">AI analysis complete</p>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-center gap-4">
              <PriorityBadge priority={result.priority} score={result.score} />
              {result.assignedTeam && (
                <span className="px-3 py-1 rounded-full bg-info-dim text-info text-xs font-mono">
                  Team: {result.assignedTeam}
                </span>
              )}
            </div>

            <div className="p-4 rounded-xl bg-muted">
              <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-wide mb-2">
                AI Reasoning
              </p>
              <p className="text-sm text-foreground">{result.reasoning}</p>
            </div>

            <Button onClick={resetForm} className="w-full">
              Submit Another Report
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
