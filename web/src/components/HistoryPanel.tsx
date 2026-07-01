import { useEffect, useState } from 'react'
import type { HistorySession } from '../lib/history'

interface HistoryPanelProps {
  open: boolean
  sessions: HistorySession[]
  activeSessionId: string | null
  onClose: () => void
  onNewDiagram: () => void
  onSelectSession: (sessionId: string) => void
  onDeleteSession: (sessionId: string) => void
  onRenameSession: (title: string) => void
}

function formatWhen(iso: string): string {
  const date = new Date(iso)
  return date.toLocaleString()
}

export function HistoryPanel({
  open,
  sessions,
  activeSessionId,
  onClose,
  onNewDiagram,
  onSelectSession,
  onDeleteSession,
  onRenameSession,
}: HistoryPanelProps) {
  const active = sessions.find((session) => session.id === activeSessionId)
  const [titleDraft, setTitleDraft] = useState(active?.title ?? '')

  useEffect(() => {
    setTitleDraft(active?.title ?? '')
  }, [active?.id, active?.title])

  if (!open) {
    return null
  }

  return (
    <aside className="history-panel" aria-label="Diagram history">
      <div className="history-panel-header">
        <h2>History</h2>
        <button type="button" className="icon-button" onClick={onClose} aria-label="Close history">
          ×
        </button>
      </div>

      <div className="history-panel-actions">
        <button type="button" onClick={onNewDiagram}>
          New diagram
        </button>
      </div>

      {active && (
        <label className="history-rename">
          Session title
          <input
            type="text"
            value={titleDraft}
            onChange={(event) => setTitleDraft(event.target.value)}
            onBlur={() => {
              if (titleDraft.trim() && titleDraft !== active.title) {
                onRenameSession(titleDraft.trim())
              }
            }}
          />
        </label>
      )}

      <ul className="history-session-list">
        {sessions.map((session) => (
          <li key={session.id}>
            <button
              type="button"
              className={`history-session-item${session.id === activeSessionId ? ' active' : ''}`}
              onClick={() => onSelectSession(session.id)}
            >
              <span className="history-session-title">{session.title}</span>
              <span className="history-session-meta">{formatWhen(session.updatedAt)}</span>
            </button>
            {sessions.length > 1 && (
              <button
                type="button"
                className="secondary history-delete-button"
                aria-label={`Delete ${session.title}`}
                onClick={() => onDeleteSession(session.id)}
              >
                Delete
              </button>
            )}
          </li>
        ))}
      </ul>
    </aside>
  )
}
