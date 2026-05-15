'use client'

import { useAppStore } from "@/lib/store"
import { PageHeader, PriorityBadge } from "@/components/rescue"
import { Button } from "@/components/ui/button"
import { Trash2 } from "lucide-react"

export default function AILogPage() {
  const { aiLog, clearAILog } = useAppStore()

  return (
    <div className="p-6">
      <PageHeader title="AI Activity Log" showTimestamp />

      {/* Log Entries */}
      <div className="mt-6 space-y-3">
        {aiLog.length === 0 ? (
          <div className="bg-card rounded-xl border p-8 text-center">
            <p className="text-muted-foreground font-mono text-sm">No AI activity logged</p>
          </div>
        ) : (
          aiLog.map(entry => (
            <div key={entry.id} className="bg-card rounded-xl border p-4">
              <div className="flex items-start gap-4">
                <div className="shrink-0">
                  <span className="text-xs font-mono text-muted-foreground">
                    {new Date(entry.timestamp).toLocaleString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit',
                      hour12: false,
                    })}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <PriorityBadge priority={entry.priority} />
                    <h3 className="font-sans font-bold text-foreground">{entry.eventTitle}</h3>
                  </div>
                  <p className="text-sm text-muted-foreground">{entry.detail}</p>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Clear Button */}
      {aiLog.length > 0 && (
        <div className="mt-6">
          <Button 
            variant="outline" 
            className="gap-1.5 text-destructive hover:text-destructive"
            onClick={clearAILog}
          >
            <Trash2 className="w-4 h-4" />
            Clear Log
          </Button>
        </div>
      )}
    </div>
  )
}
