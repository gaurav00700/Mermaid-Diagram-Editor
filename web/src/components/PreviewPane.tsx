import { memo, useEffect, useRef, useState } from 'react'
import type { BindFunctions } from '../hooks/useMermaid'

interface PreviewPaneProps {
  svg: string
  error: string | null
  isRendering: boolean
  bindFunctions: BindFunctions
}

export const PreviewPane = memo(function PreviewPane({
  svg,
  error,
  isRendering,
  bindFunctions,
}: PreviewPaneProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const viewportRef = useRef<HTMLDivElement>(null)
  const [scale, setScale] = useState(1)
  const [offset, setOffset] = useState({ x: 0, y: 0 })
  const dragRef = useRef<{ startX: number; startY: number; originX: number; originY: number } | null>(
    null,
  )

  useEffect(() => {
    const container = containerRef.current
    if (!container) {
      return
    }

    container.innerHTML = svg
    bindFunctions?.(container)
  }, [svg, bindFunctions])

  useEffect(() => {
    setScale(1)
    setOffset({ x: 0, y: 0 })
  }, [svg])

  const handleWheel = (event: React.WheelEvent<HTMLDivElement>) => {
    event.preventDefault()
    const delta = event.deltaY < 0 ? 0.1 : -0.1
    setScale((current) => Math.max(0.01, Number((current + delta).toFixed(2))))
  }

  const handleMouseDown = (event: React.MouseEvent<HTMLDivElement>) => {
    if (event.button !== 0) {
      return
    }
    dragRef.current = {
      startX: event.clientX,
      startY: event.clientY,
      originX: offset.x,
      originY: offset.y,
    }
  }

  const handleMouseMove = (event: React.MouseEvent<HTMLDivElement>) => {
    if (!dragRef.current) {
      return
    }
    setOffset({
      x: dragRef.current.originX + (event.clientX - dragRef.current.startX),
      y: dragRef.current.originY + (event.clientY - dragRef.current.startY),
    })
  }

  const stopDragging = () => {
    dragRef.current = null
  }

  const zoomIn = () => setScale((current) => Number((current + 0.1).toFixed(2)))
  const zoomOut = () => setScale((current) => Math.max(0.01, Number((current - 0.1).toFixed(2))))
  const resetView = () => {
    setScale(1)
    setOffset({ x: 0, y: 0 })
  }

  return (
    <div className="preview-pane">
      <div className="preview-header">
        <span>Preview</span>
        <div className="preview-header-actions">
          {isRendering && <span className="preview-status">Rendering…</span>}
          <div className="preview-zoom-controls">
            <button type="button" className="secondary zoom-button" onClick={zoomOut} aria-label="Zoom out">
              −
            </button>
            <span className="preview-zoom-label">{Math.round(scale * 100)}%</span>
            <button type="button" className="secondary zoom-button" onClick={zoomIn} aria-label="Zoom in">
              +
            </button>
            <button type="button" className="secondary zoom-button" onClick={resetView}>
              Reset view
            </button>
          </div>
        </div>
      </div>
      <div
        ref={viewportRef}
        className="preview-body preview-viewport"
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={stopDragging}
        onMouseLeave={stopDragging}
      >
        {error && <div className="preview-error">{error}</div>}
        {!error && !svg && !isRendering && (
          <div className="preview-empty">Enter Mermaid code to see a preview.</div>
        )}
        {!error && svg && (
          <div
            className="preview-canvas"
            style={{
              transform: `translate(${offset.x}px, ${offset.y}px) scale(${scale})`,
            }}
          >
            <div ref={containerRef} className="preview-svg" />
          </div>
        )}
      </div>
    </div>
  )
})
