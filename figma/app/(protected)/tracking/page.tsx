'use client'

import { useState, useEffect } from 'react'
import { useAppStore } from "@/lib/store"
import { PageHeader, SectionHeader, CaseIdBadge, OnlineBadge } from "@/components/rescue"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { MapPin, Save, Navigation } from "lucide-react"
import dynamic from 'next/dynamic'

// Dynamically import the map to avoid SSR issues
const TrackingMap = dynamic(() => import('./tracking-map'), { 
  ssr: false,
  loading: () => (
    <div className="w-full h-[460px] rounded-xl bg-[#0C1220] flex items-center justify-center">
      <span className="text-muted-foreground font-mono text-sm">Loading map...</span>
    </div>
  )
})

const statusOptions = [
  { value: 'searching', label: 'Searching' },
  { value: 'on_scene', label: 'On Scene' },
  { value: 'returning', label: 'Returning' },
  { value: 'standby', label: 'Standby' },
]

export default function TrackingPage() {
  const { currentUser, volunteers, cases, checkIns, addCheckIn } = useAppStore()
  const [myAddress, setMyAddress] = useState('')
  const [gpsStatus, setGpsStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [gpsLat, setGpsLat] = useState('')
  const [gpsLon, setGpsLon] = useState('')
  
  // Check-in form
  const [checkInAddress, setCheckInAddress] = useState('')
  const [checkInStatus, setCheckInStatus] = useState('searching')
  const [checkInArea, setCheckInArea] = useState('')
  const [checkInCase, setCheckInCase] = useState('')
  const [checkInNotes, setCheckInNotes] = useState('')

  const [activeTab, setActiveTab] = useState<'history' | 'raw'>('history')

  const activeCases = cases.filter(c => c.status === 'active' || c.status === 'assigned')

  const handleGetGPS = () => {
    setGpsStatus('loading')
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setGpsLat(position.coords.latitude.toFixed(6))
          setGpsLon(position.coords.longitude.toFixed(6))
          setGpsStatus('success')
        },
        () => {
          setGpsStatus('error')
        }
      )
    } else {
      setGpsStatus('error')
    }
  }

  const handleCheckIn = (e: React.FormEvent) => {
    e.preventDefault()
    if (!currentUser) return

    addCheckIn({
      volunteerId: currentUser.id,
      volunteerName: currentUser.name,
      address: checkInAddress,
      status: checkInStatus,
      gpsLat: gpsLat ? parseFloat(gpsLat) : undefined,
      gpsLon: gpsLon ? parseFloat(gpsLon) : undefined,
      area: checkInArea,
      caseId: checkInCase || undefined,
      notes: checkInNotes,
    })

    // Reset form
    setCheckInAddress('')
    setCheckInStatus('searching')
    setCheckInArea('')
    setCheckInCase('')
    setCheckInNotes('')
    setGpsLat('')
    setGpsLon('')
    setGpsStatus('idle')
  }

  const getStatusEmoji = (status: string) => {
    const emojis: Record<string, string> = {
      searching: '🔍',
      on_scene: '📍',
      returning: '🏠',
      standby: '⏸️',
    }
    return emojis[status] || '❓'
  }

  return (
    <div className="p-6">
      <PageHeader title="Tracking" showTimestamp />

      {/* My Position Section */}
      <div className="mt-6 bg-card rounded-xl border p-4">
        <SectionHeader label="My Position" className="mb-0" />
        <div className="mt-4 flex items-center gap-4">
          <Input
            value={myAddress}
            onChange={(e) => setMyAddress(e.target.value)}
            placeholder="Enter your current address"
            className="flex-1 h-10 rounded-[14px] font-mono"
          />
          <Button variant="outline" className="gap-1.5 shrink-0">
            <Save className="w-4 h-4" />
            Save Position
          </Button>
        </div>
      </div>

      {/* GPS Acquisition */}
      <div className="mt-4 bg-card rounded-xl border p-4">
        <div className="flex items-center gap-4">
          <Button 
            onClick={handleGetGPS} 
            variant="outline" 
            className="gap-1.5"
            disabled={gpsStatus === 'loading'}
          >
            <Navigation className="w-4 h-4" />
            Get my GPS location
          </Button>
          <span className="text-xs font-mono text-muted-foreground">
            {gpsStatus === 'idle' && 'Click to acquire GPS coordinates'}
            {gpsStatus === 'loading' && 'Acquiring location...'}
            {gpsStatus === 'success' && `Location acquired: ${gpsLat}, ${gpsLon}`}
            {gpsStatus === 'error' && 'Failed to get location. Check browser permissions.'}
          </span>
        </div>
      </div>

      {/* Check-in Form */}
      <form onSubmit={handleCheckIn} className="mt-6 bg-card rounded-xl border p-6 space-y-4">
        <SectionHeader label="Check-In Form" className="mb-0" />
        
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label className="text-xs font-mono uppercase tracking-wide">Address</Label>
            <Input
              value={checkInAddress}
              onChange={(e) => setCheckInAddress(e.target.value)}
              placeholder="Current location address"
              className="h-10 rounded-[14px] font-mono"
              required
            />
          </div>
          <div className="space-y-2">
            <Label className="text-xs font-mono uppercase tracking-wide">Field Status</Label>
            <select
              value={checkInStatus}
              onChange={(e) => setCheckInStatus(e.target.value)}
              className="w-full h-10 px-3 rounded-[14px] border border-input bg-background text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {statusOptions.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label className="text-xs font-mono uppercase tracking-wide">GPS Latitude</Label>
            <Input
              value={gpsLat}
              onChange={(e) => setGpsLat(e.target.value)}
              placeholder="e.g. 40.7128"
              className="h-10 rounded-[14px] font-mono"
            />
          </div>
          <div className="space-y-2">
            <Label className="text-xs font-mono uppercase tracking-wide">GPS Longitude</Label>
            <Input
              value={gpsLon}
              onChange={(e) => setGpsLon(e.target.value)}
              placeholder="e.g. -74.0060"
              className="h-10 rounded-[14px] font-mono"
            />
          </div>
          <div className="space-y-2">
            <Label className="text-xs font-mono uppercase tracking-wide">Area</Label>
            <Input
              value={checkInArea}
              onChange={(e) => setCheckInArea(e.target.value)}
              placeholder="e.g. Section B"
              className="h-10 rounded-[14px] font-mono"
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label className="text-xs font-mono uppercase tracking-wide">Active Case (Optional)</Label>
          <select
            value={checkInCase}
            onChange={(e) => setCheckInCase(e.target.value)}
            className="w-full h-10 px-3 rounded-[14px] border border-input bg-background text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">None</option>
            {activeCases.map(c => (
              <option key={c.id} value={c.id}>{c.id} - {c.name}</option>
            ))}
          </select>
        </div>

        <div className="space-y-2">
          <Label className="text-xs font-mono uppercase tracking-wide">Notes</Label>
          <Textarea
            value={checkInNotes}
            onChange={(e) => setCheckInNotes(e.target.value)}
            placeholder="Additional observations..."
            className="rounded-[14px] font-mono min-h-[80px]"
          />
        </div>

        <Button type="submit" className="w-full gap-1.5">
          <MapPin className="w-4 h-4" />
          Submit Check-In
        </Button>
      </form>

      {/* Map */}
      <div className="mt-6">
        <SectionHeader label="Live Map" />
        <TrackingMap volunteers={volunteers} cases={cases} />
      </div>

      {/* Log Tabs */}
      <div className="mt-6">
        <div className="flex items-center bg-muted rounded-lg p-1 w-fit mb-4">
          <button
            onClick={() => setActiveTab('history')}
            className={`px-4 py-2 rounded-md text-sm font-mono transition-colors ${
              activeTab === 'history' ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground'
            }`}
          >
            Check-In History
          </button>
          <button
            onClick={() => setActiveTab('raw')}
            className={`px-4 py-2 rounded-md text-sm font-mono transition-colors ${
              activeTab === 'raw' ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground'
            }`}
          >
            Raw Heartbeat DB
          </button>
        </div>

        {activeTab === 'history' && (
          <div className="space-y-3">
            {checkIns.length === 0 ? (
              <div className="bg-card rounded-xl border p-8 text-center">
                <p className="text-muted-foreground font-mono text-sm">No check-ins recorded yet</p>
              </div>
            ) : (
              checkIns.slice().reverse().map(checkIn => (
                <div key={checkIn.id} className="bg-card rounded-xl border p-4">
                  <div className="flex items-center gap-3">
                    <span className="text-xl">{getStatusEmoji(checkIn.status)}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-sans font-bold text-foreground">{checkIn.volunteerName}</span>
                        <span className="text-xs font-mono text-muted-foreground">
                          {new Date(checkIn.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground">{checkIn.address}</p>
                    </div>
                    {checkIn.caseId && <CaseIdBadge caseId={checkIn.caseId} />}
                  </div>
                  {checkIn.notes && (
                    <p className="mt-2 text-xs font-mono text-muted-foreground border-l-2 border-border pl-3">
                      {checkIn.notes}
                    </p>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'raw' && (
          <div className="bg-card rounded-xl border p-4">
            <div className="font-mono text-xs space-y-1">
              {checkIns.length === 0 ? (
                <p className="text-muted-foreground">No heartbeat data</p>
              ) : (
                checkIns.slice().reverse().map(checkIn => (
                  <div key={checkIn.id} className="flex gap-4 text-muted-foreground">
                    <span>{new Date(checkIn.timestamp).toISOString()}</span>
                    <span className="text-foreground">{checkIn.volunteerName}</span>
                    <span>{checkIn.status}</span>
                    <span>{checkIn.gpsLat && checkIn.gpsLon ? `${checkIn.gpsLat},${checkIn.gpsLon}` : 'NO_GPS'}</span>
                  </div>
                ))
              )}
            </div>
            <div className="mt-4 p-3 rounded-lg bg-muted text-xs font-mono text-muted-foreground">
              <p>API Endpoint: <code className="text-foreground">/api/heartbeat</code></p>
              <p>Method: POST | Auth: Bearer Token</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
