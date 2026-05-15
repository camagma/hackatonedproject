'use client'

import { useState } from 'react'
import { useAppStore } from "@/lib/store"
import { PageHeader, SectionHeader, VolunteerAvatar, OnlineBadge } from "@/components/rescue"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ChevronDown, ChevronUp, Plus, Power, PowerOff } from "lucide-react"

const skillOptions = [
  'Medical',
  'K9 Handler',
  'Drone Operator',
  'First Aid',
  'Navigation',
  'Communications',
  'Wilderness Survival',
  'Climbing',
  'Water Rescue',
  'Roadside Assistance',
]

export default function VolunteersPage() {
  const { volunteers, cases, addVolunteer, updateVolunteer } = useAppStore()
  const [showAddForm, setShowAddForm] = useState(false)
  const [newName, setNewName] = useState('')
  const [newSkill, setNewSkill] = useState('')
  const [newAddress, setNewAddress] = useState('')

  const onlineCount = volunteers.filter(v => v.status === 'active').length
  const offlineCount = volunteers.filter(v => v.status === 'offline').length
  const unknownCount = volunteers.filter(v => !v.status || v.status === 'busy').length

  const getNearbyCases = (volunteerId: string) => {
    // In a real app, this would calculate proximity
    return cases.filter(c => c.status === 'active' || c.status === 'assigned').length
  }

  const handleAddVolunteer = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newName || !newSkill || !newAddress) return

    addVolunteer({
      id: `v-${Date.now()}`,
      name: newName,
      username: newName.toLowerCase().replace(' ', '_'),
      role: 'volunteer',
      skills: [newSkill],
      address: newAddress,
      status: 'offline',
      lastPing: new Date(),
      deviceId: `DEV-${Date.now().toString(36).toUpperCase()}`,
    })

    setNewName('')
    setNewSkill('')
    setNewAddress('')
    setShowAddForm(false)
  }

  const toggleVolunteerStatus = (id: string, currentStatus: string | undefined) => {
    updateVolunteer(id, {
      status: currentStatus === 'active' ? 'offline' : 'active',
      lastPing: new Date(),
    })
  }

  return (
    <div className="p-6">
      <PageHeader title="Volunteers" showTimestamp />

      {/* Online Summary Strip */}
      <div className="mt-6 bg-card rounded-xl border p-4 flex items-center gap-6 text-xs font-mono">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-online" />
          <span className="text-online font-semibold">{onlineCount}</span>
          <span className="text-muted-foreground">online</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-offline" />
          <span className="text-offline font-semibold">{offlineCount}</span>
          <span className="text-muted-foreground">offline</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-unknown" />
          <span className="text-unknown font-semibold">{unknownCount}</span>
          <span className="text-muted-foreground">unknown</span>
        </div>
        <span className="text-muted-foreground ml-auto">
          Last sync: {new Date().toLocaleTimeString()}
        </span>
      </div>

      {/* Add Volunteer Form */}
      <div className="mt-6">
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="flex items-center gap-2 text-sm font-sans font-bold text-foreground hover:text-primary transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Volunteer
          {showAddForm ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showAddForm && (
          <form onSubmit={handleAddVolunteer} className="mt-4 bg-card rounded-xl border p-6 space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label className="text-xs font-mono uppercase tracking-wide">Name</Label>
                <Input
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="Full name"
                  className="h-10 rounded-[14px] font-mono"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label className="text-xs font-mono uppercase tracking-wide">Skill</Label>
                <select
                  value={newSkill}
                  onChange={(e) => setNewSkill(e.target.value)}
                  className="w-full h-10 px-3 rounded-[14px] border border-input bg-background text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                >
                  <option value="">Select skill</option>
                  {skillOptions.map(skill => (
                    <option key={skill} value={skill}>{skill}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label className="text-xs font-mono uppercase tracking-wide">Address</Label>
                <Input
                  value={newAddress}
                  onChange={(e) => setNewAddress(e.target.value)}
                  placeholder="Enter address"
                  className="h-10 rounded-[14px] font-mono"
                  required
                />
              </div>
            </div>
            <p className="text-[10px] font-mono text-muted-foreground">
              Address is used for proximity-based case assignment
            </p>
            <Button type="submit" size="sm">
              Add Volunteer
            </Button>
          </form>
        )}
      </div>

      {/* Volunteer Cards */}
      <div className="mt-6 space-y-4">
        {volunteers.map(volunteer => (
          <div key={volunteer.id} className="bg-card rounded-xl border p-4">
            {/* Top Row */}
            <div className="flex items-center gap-4">
              <VolunteerAvatar name={volunteer.name} status={volunteer.status} size="lg" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="font-sans font-bold text-foreground">{volunteer.name}</h3>
                  <span className="px-2 py-0.5 rounded bg-info-dim text-info text-[10px] font-mono uppercase">
                    {volunteer.skills?.[0] || 'No skill'}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-muted text-muted-foreground text-[10px] font-mono uppercase">
                    {volunteer.status || 'unknown'}
                  </span>
                </div>
                <OnlineBadge 
                  status={volunteer.status === 'active' ? 'online' : volunteer.status === 'offline' ? 'offline' : 'unknown'} 
                  lastPing={volunteer.lastPing} 
                  className="mt-1"
                />
              </div>
            </div>

            {/* Detail Grid */}
            <div className="mt-4 grid grid-cols-2 gap-x-8 gap-y-2 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Last Ping:</span>
                <span className="text-foreground">{volunteer.lastPing ? new Date(volunteer.lastPing).toLocaleString() : 'Never'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Source:</span>
                <span className="text-foreground">Manual</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Device ID:</span>
                <span className="text-foreground">{volunteer.deviceId || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Nearby Cases:</span>
                <span className="text-foreground">{getNearbyCases(volunteer.id)}</span>
              </div>
              <div className="flex justify-between col-span-2">
                <span className="text-muted-foreground">Address:</span>
                <span className="text-foreground">{volunteer.address || 'Not set'}</span>
              </div>
            </div>

            {/* Actions */}
            <div className="mt-4 pt-4 border-t border-border flex items-center gap-2">
              <Button 
                size="sm" 
                variant={volunteer.status === 'active' ? 'outline' : 'default'}
                className="gap-1.5"
                onClick={() => toggleVolunteerStatus(volunteer.id, volunteer.status)}
              >
                {volunteer.status === 'active' ? (
                  <>
                    <PowerOff className="w-3.5 h-3.5" />
                    Set Offline
                  </>
                ) : (
                  <>
                    <Power className="w-3.5 h-3.5" />
                    Activate
                  </>
                )}
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
