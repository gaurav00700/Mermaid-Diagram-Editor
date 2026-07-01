import { useCallback, useEffect, useRef, useState } from 'react'
import { EditorPane } from './components/EditorPane'
import { ExportDialog } from './components/ExportDialog'
import { HistoryPanel } from './components/HistoryPanel'
import { PreviewPane } from './components/PreviewPane'
import { Toolbar } from './components/Toolbar'
import { useHistory } from './hooks/useHistory'
import { useMermaid } from './hooks/useMermaid'
import { DEFAULT_DIAGRAM } from './lib/defaultDiagram'
import { downloadSource } from './lib/downloadSource'
import { exportDiagram } from './lib/exportDiagram'
import { EXPORT_OPTIONS, type ExportSettings } from './lib/exportOptions'
import './styles/app.css'

export default function App() {
  const {
    sessions,
    activeSession,
    activeSessionId,
    editorKey,
    updateActiveCode,
    createSession,
    switchSession,
    removeSession,
    renameActiveSession,
    replaceActiveCode,
  } = useHistory()

  const [splitRatio, setSplitRatio] = useState(0.5)
  const [isDragging, setIsDragging] = useState(false)
  const [historyOpen, setHistoryOpen] = useState(false)
  const [exportOpen, setExportOpen] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const layoutRef = useRef<HTMLDivElement>(null)
  const isFirstRenderRef = useRef(true)

  const code = activeSession.code
  const { svg, error, isRendering, bindFunctions, render } = useMermaid('default')

  useEffect(() => {
    if (isFirstRenderRef.current) {
      isFirstRenderRef.current = false
      void render(code)
      return
    }

    const timer = window.setTimeout(() => {
      void render(code)
    }, 250)

    return () => window.clearTimeout(timer)
  }, [code, render])

  useEffect(() => {
    if (!isDragging) {
      return
    }

    const handleMouseMove = (event: MouseEvent) => {
      const layout = layoutRef.current
      if (!layout) {
        return
      }
      const rect = layout.getBoundingClientRect()
      const nextRatio = (event.clientX - rect.left) / rect.width
      setSplitRatio(Math.min(0.75, Math.max(0.25, nextRatio)))
    }

    const handleMouseUp = () => setIsDragging(false)

    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('mouseup', handleMouseUp)
    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isDragging])

  const handleUpload = useCallback(
    (content: string) => {
      if (!content) {
        setUploadError('Could not read the selected file.')
        return
      }
      setUploadError(null)
      replaceActiveCode(content)
    },
    [replaceActiveCode],
  )

  const handleReset = useCallback(() => {
    setUploadError(null)
    replaceActiveCode(DEFAULT_DIAGRAM)
  }, [replaceActiveCode])

  const handleExport = useCallback(
    async (settings: ExportSettings) => {
      setIsExporting(true)
      setExportError(null)
      try {
        const exportSvg = await render(code, settings.theme, {
          forExport: true,
          securityLevel: settings.format === 'png' ? 'strict' : 'loose',
          htmlLabels: settings.format !== 'png',
        })
        if (!exportSvg) {
          throw new Error('Nothing to export. Fix diagram errors first.')
        }
        await exportDiagram(exportSvg, settings)
        setExportOpen(false)
      } catch (err) {
        setExportError(err instanceof Error ? err.message : 'Export failed')
      } finally {
        setIsExporting(false)
        void render(code)
      }
    },
    [code, render],
  )

  const handleDownloadSource = useCallback(() => {
    downloadSource(code, EXPORT_OPTIONS.defaultSourceFilename)
  }, [code])

  return (
    <div className="app">
      <Toolbar
        onUpload={handleUpload}
        onDownloadSource={handleDownloadSource}
        onExport={() => {
          setExportError(null)
          setExportOpen(true)
        }}
        onReset={handleReset}
        onToggleHistory={() => setHistoryOpen((current) => !current)}
        uploadError={uploadError}
      />

      <div className="app-body">
        <HistoryPanel
          open={historyOpen}
          sessions={sessions}
          activeSessionId={activeSessionId}
          onClose={() => setHistoryOpen(false)}
          onNewDiagram={() => createSession()}
          onSelectSession={switchSession}
          onDeleteSession={removeSession}
          onRenameSession={renameActiveSession}
        />

        <div className="workspace" ref={layoutRef}>
          <div className="pane editor-container" style={{ width: `${splitRatio * 100}%` }}>
            <EditorPane code={code} onChange={updateActiveCode} editorKey={editorKey} />
          </div>
          <div
            className={`split-handle${isDragging ? ' dragging' : ''}`}
            onMouseDown={() => setIsDragging(true)}
            role="separator"
            aria-orientation="vertical"
            aria-label="Resize panes"
          />
          <div className="pane preview-container" style={{ width: `${(1 - splitRatio) * 100}%` }}>
            <PreviewPane
              svg={svg}
              error={error}
              isRendering={isRendering}
              bindFunctions={bindFunctions}
            />
          </div>
        </div>
      </div>

      <ExportDialog
        open={exportOpen}
        onClose={() => setExportOpen(false)}
        onExport={handleExport}
        isExporting={isExporting}
        exportError={exportError}
      />
    </div>
  )
}
