import { useCallback, useMemo, useState } from 'react'
import { DEFAULT_DIAGRAM } from '../lib/defaultDiagram'
import {
  createNewSession,
  deleteSessionFromStore,
  getActiveSession,
  loadActiveSessionId,
  loadHistoryStore,
  renameSession,
  saveActiveSessionId,
  updateSessionCode,
  upsertSession,
  type HistorySession,
} from '../lib/history'

export function useHistory() {
  const [store, setStore] = useState(() => loadHistoryStore())
  const [activeSessionId, setActiveSessionId] = useState(() => {
    const id = loadActiveSessionId()
    if (id && store.sessions.some((session) => session.id === id)) {
      return id
    }
    const first = store.sessions[0]?.id ?? null
    if (first) {
      saveActiveSessionId(first)
    }
    return first
  })
  const [editorKey, setEditorKey] = useState(0)

  const activeSession = useMemo(
    () => getActiveSession(store, activeSessionId),
    [store, activeSessionId],
  )

  const refreshEditor = useCallback(() => {
    setEditorKey((current) => current + 1)
  }, [])

  const setActiveSession = useCallback((session: HistorySession) => {
    saveActiveSessionId(session.id)
    setActiveSessionId(session.id)
    refreshEditor()
  }, [refreshEditor])

  const updateActiveCode = useCallback(
    (code: string) => {
      setStore((current) => {
        const session = getActiveSession(current, activeSessionId)
        const updated = updateSessionCode(session, code)
        return upsertSession(current, updated)
      })
    },
    [activeSessionId],
  )

  const createSession = useCallback(
    (code: string = DEFAULT_DIAGRAM, title?: string) => {
      const session = createNewSession(code, title)
      const next = upsertSession(store, session)
      setStore(next)
      setActiveSession(session)
    },
    [setActiveSession, store],
  )

  const switchSession = useCallback(
    (sessionId: string) => {
      const session = store.sessions.find((item) => item.id === sessionId)
      if (!session) {
        return
      }
      setActiveSession(session)
    },
    [setActiveSession, store.sessions],
  )

  const removeSession = useCallback(
    (sessionId: string) => {
      if (store.sessions.length <= 1) {
        return false
      }
      const next = deleteSessionFromStore(store, sessionId)
      setStore(next)
      if (activeSessionId === sessionId) {
        const fallback = next.sessions[0]
        setActiveSession(fallback)
      }
      return true
    },
    [activeSessionId, setActiveSession, store],
  )

  const renameActiveSession = useCallback(
    (title: string) => {
      const updated = renameSession(activeSession, title)
      setStore((current) => upsertSession(current, updated))
    },
    [activeSession],
  )

  const replaceActiveCode = useCallback(
    (code: string) => {
      const updated = updateSessionCode(activeSession, code)
      setStore((current) => upsertSession(current, updated))
      refreshEditor()
    },
    [activeSession, refreshEditor],
  )

  return {
    sessions: store.sessions,
    activeSession,
    activeSessionId,
    editorKey,
    updateActiveCode,
    createSession,
    switchSession,
    removeSession,
    renameActiveSession,
    replaceActiveCode,
  }
}
