import { useCallback, useEffect, useRef, useState } from 'react'
import { EditorPane } from './components/EditorPane'
import { ExportDialog } from './components/ExportDialog'
import { PreviewPane } from './components/PreviewPane'
import { Toolbar } from './components/Toolbar'
import { useMermaid } from './hooks/useMermaid'
import { DEFAULT_DIAGRAM, STORAGE_KEY } from './lib/defaultDiagram'
import { exportDiagram } from './lib/exportDiagram'
import type { ExportSettings } from './lib/exportOptions'
import './styles/app.css'

function loadInitialCode(): string {
  const saved = localStorage.getItem(STORAGE_KEY)
  return saved ?? DEFAULT_DIAGRAM
}

export default function App() {
  const [code, setCode] = useState(loadInitialCode)
  const [editorKey, setEditorKey] = useState(0)
  const [splitRatio, setSplitRatio] = useState(0.5)
  const [isDragging, setIsDragging] = useState(false)
  const [exportOpen, setExportOpen] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const layoutRef = useRef<HTMLDivElement>(null)
  const isFirstRenderRef = useRef(true)

  const { svg, error, isRendering, bindFunctions, render } = useMermaid('default')

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, code)
  }, [code])

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

  const replaceCode = useCallback((nextCode: string) => {
    setCode(nextCode)
    setEditorKey((current) => current + 1)
  }, [])

  const handleUpload = useCallback(
    (content: string) => {
      if (!content) {
        setUploadError('Could not read the selected file.')
        return
      }
      setUploadError(null)
      replaceCode(content)
    },
    [replaceCode],
  )

  const handleReset = useCallback(() => {
    setUploadError(null)
    replaceCode(DEFAULT_DIAGRAM)
  }, [replaceCode])

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

  return (
    <div className="app">
      <Toolbar
        onUpload={handleUpload}
        onDownload={() => {
          setExportError(null)
          setExportOpen(true)
        }}
        onReset={handleReset}
        uploadError={uploadError}
      />

      <div className="workspace" ref={layoutRef}>
        <div className="pane editor-container" style={{ width: `${splitRatio * 100}%` }}>
          <EditorPane code={code} onChange={setCode} editorKey={editorKey} />
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
