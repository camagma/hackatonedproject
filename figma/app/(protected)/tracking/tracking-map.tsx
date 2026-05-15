'use client'

import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { User, Case } from '@/lib/store'

interface TrackingMapProps {
  volunteers: User[]
  cases: Case[]
}

export default function TrackingMap({ volunteers, cases }: TrackingMapProps) {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<L.Map | null>(null)

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return

    // Initialize map
    const map = L.map(mapRef.current, {
      center: [40.7128, -74.0060], // NYC default
      zoom: 12,
      zoomControl: true,
    })

    // Dark tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '',
      maxZoom: 19,
    }).addTo(map)

    mapInstanceRef.current = map

    // Add volunteer markers
    volunteers.forEach((volunteer, index) => {
      const lat = 40.7128 + (Math.random() - 0.5) * 0.05
      const lng = -74.0060 + (Math.random() - 0.5) * 0.05
      
      const statusColor = volunteer.status === 'active' ? '#16A34A' : 
                          volunteer.status === 'offline' ? '#DC2626' : '#6B7280'

      const markerIcon = L.divIcon({
        className: 'custom-marker',
        html: `
          <div style="
            width: 24px;
            height: 24px;
            background: ${statusColor};
            border: 2px solid white;
            border-radius: 50%;
            box-shadow: 0 2px 8px rgba(0,0,0,0.4);
          "></div>
          <div style="
            position: absolute;
            top: 28px;
            left: 50%;
            transform: translateX(-50%);
            white-space: nowrap;
            color: white;
            font-size: 10px;
            font-family: monospace;
            text-shadow: 0 1px 3px rgba(0,0,0,0.8);
          ">${volunteer.name.split(' ')[0]}</div>
        `,
        iconSize: [24, 40],
        iconAnchor: [12, 12],
      })

      L.marker([lat, lng], { icon: markerIcon })
        .addTo(map)
        .bindPopup(`
          <div style="font-family: monospace; font-size: 12px;">
            <strong>${volunteer.name}</strong><br/>
            Status: ${volunteer.status || 'unknown'}<br/>
            Skills: ${volunteer.skills?.join(', ') || 'None'}
          </div>
        `)
    })

    // Add case markers
    const activeCases = cases.filter(c => c.status === 'active' || c.status === 'assigned')
    activeCases.forEach((caseData, index) => {
      const lat = 40.7128 + (Math.random() - 0.5) * 0.08
      const lng = -74.0060 + (Math.random() - 0.5) * 0.08

      const priorityColors: Record<string, string> = {
        critical: '#DC2626',
        high: '#EA580C',
        medium: '#CA8A04',
        low: '#16A34A',
      }
      const color = priorityColors[caseData.priority] || '#6B7280'

      // Dashed circle for cases
      L.circle([lat, lng], {
        radius: 200,
        color: color,
        fillColor: color,
        fillOpacity: 0.15,
        weight: 2,
        dashArray: '8, 8',
      })
        .addTo(map)
        .bindPopup(`
          <div style="font-family: monospace; font-size: 12px;">
            <strong>${caseData.id}</strong><br/>
            ${caseData.name}, ${caseData.age}<br/>
            Priority: ${caseData.priority.toUpperCase()}<br/>
            ${caseData.lastKnownAddress}
          </div>
        `)
    })

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove()
        mapInstanceRef.current = null
      }
    }
  }, [volunteers, cases])

  return (
    <div className="relative">
      <div ref={mapRef} className="w-full h-[460px] rounded-xl overflow-hidden" />
      
      {/* Legend */}
      <div className="absolute bottom-4 right-4 bg-[#0C1220]/90 backdrop-blur-sm rounded-lg p-3 border border-[#2D3A4F]">
        <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-wide mb-2">Legend</p>
        <div className="space-y-1.5 text-xs font-mono">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-online" />
            <span className="text-white/80">Online Volunteer</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-offline" />
            <span className="text-white/80">Offline Volunteer</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full border-2 border-dashed border-critical" />
            <span className="text-white/80">Critical Case</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full border-2 border-dashed border-high" />
            <span className="text-white/80">High Priority</span>
          </div>
        </div>
      </div>
    </div>
  )
}
