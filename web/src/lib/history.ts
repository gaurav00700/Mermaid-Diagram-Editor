import { DEFAULT_DIAGRAM, LEGACY_STORAGE_KEY } from './defaultDiagram'
import { EXPORT_OPTIONS } from './exportOptions'

export const SESSIONS_STORAGE_KEY = 'mermaid-diagram-sessions'
export const ACTIVE_SESSION_STORAGE_KEY = 'mermaid-diagram-active-session-id'

export interface HistorySession {
  id: string
  title: string
  code: string
  createdAt: string
  updatedAt: string
}

interface HistoryStore {
  sessions: HistorySession[]
}

function nowIso(): string {
  return new Date().toISOString()
}

export function autoTitle(code: string): string {
  const firstLine = code
    .split('\n')
    .map((line) => line.trim())
    .find(Boolean)
  if (!firstLine) {
    return 'Untitled diagram'
  }
  return firstLine.length > 48 ? `${firstLine.slice(0, 45)}...` : firstLine
}

function createSession(code: string, title?: string): HistorySession {
  const timestamp = nowIso()
  return {
    id: crypto.randomUUID(),
    title: title ?? autoTitle(code),
    code,
    createdAt: timestamp,
    updatedAt: timestamp,
  }
}

function trimSessions(sessions: HistorySession[]): HistorySession[] {
  const max = EXPORT_OPTIONS.maxHistoryEntries
  if (sessions.length <= max) {
    return sessions
  }
  return sessions
    .slice()
    .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))
    .slice(0, max)
}

function readStore(): HistoryStore {
  const raw = localStorage.getItem(SESSIONS_STORAGE_KEY)
  if (!raw) {
    return { sessions: [] }
  }
  try {
    const parsed = JSON.parse(raw) as HistoryStore
    if (!Array.isArray(parsed.sessions)) {
      return { sessions: [] }
    }
    return { sessions: parsed.sessions }
  } catch {
    return { sessions: [] }
  }
}

function writeStore(store: HistoryStore): void {
  localStorage.setItem(
    SESSIONS_STORAGE_KEY,
    JSON.stringify({ sessions: trimSessions(store.sessions) }),
  )
}

function migrateLegacyStorage(): HistoryStore {
  const legacy = localStorage.getItem(LEGACY_STORAGE_KEY)
  const code = legacy ?? DEFAULT_DIAGRAM
  const session = createSession(code)
  const store = { sessions: [session] }
  writeStore(store)
  localStorage.setItem(ACTIVE_SESSION_STORAGE_KEY, session.id)
  localStorage.removeItem(LEGACY_STORAGE_KEY)
  return store
}

export function loadHistoryStore(): HistoryStore {
  const store = readStore()
  if (store.sessions.length === 0) {
    return migrateLegacyStorage()
  }
  return store
}

export function loadActiveSessionId(): string | null {
  return localStorage.getItem(ACTIVE_SESSION_STORAGE_KEY)
}

export function saveActiveSessionId(id: string): void {
  localStorage.setItem(ACTIVE_SESSION_STORAGE_KEY, id)
}

export function getActiveSession(store: HistoryStore, activeId: string | null): HistorySession {
  if (activeId) {
    const found = store.sessions.find((session) => session.id === activeId)
    if (found) {
      return found
    }
  }
  return store.sessions[0]
}

export function upsertSession(store: HistoryStore, session: HistorySession): HistoryStore {
  const index = store.sessions.findIndex((item) => item.id === session.id)
  const sessions =
    index === -1
      ? [session, ...store.sessions]
      : store.sessions.map((item, i) => (i === index ? session : item))
  const next = { sessions: trimSessions(sessions) }
  writeStore(next)
  return next
}

export function createNewSession(code: string = DEFAULT_DIAGRAM, title?: string): HistorySession {
  return createSession(code, title)
}

export function updateSessionCode(session: HistorySession, code: string): HistorySession {
  return {
    ...session,
    code,
    title: session.title === autoTitle(session.code) ? autoTitle(code) : session.title,
    updatedAt: nowIso(),
  }
}

export function renameSession(session: HistorySession, title: string): HistorySession {
  return {
    ...session,
    title: title.trim() || autoTitle(session.code),
    updatedAt: nowIso(),
  }
}

export function deleteSessionFromStore(store: HistoryStore, sessionId: string): HistoryStore {
  const sessions = store.sessions.filter((session) => session.id !== sessionId)
  const next = { sessions }
  writeStore(next)
  return next
}
