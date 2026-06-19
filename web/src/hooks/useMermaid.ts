import { useCallback, useEffect, useRef, useState } from 'react'
import mermaid from 'mermaid'
import type { MermaidTheme } from '../lib/exportOptions'

type BindFunctions = ((element: Element) => void) | undefined

export type { BindFunctions }

export interface RenderOptions {
  forExport?: boolean
  securityLevel?: 'strict' | 'loose' | 'antiscript' | 'sandbox'
  htmlLabels?: boolean
}

interface UseMermaidResult {
  svg: string
  error: string | null
  isRendering: boolean
  bindFunctions: BindFunctions
  render: (code: string, theme?: MermaidTheme, options?: RenderOptions) => Promise<string | null>
}

export function useMermaid(theme: MermaidTheme = 'default'): UseMermaidResult {
  const [svg, setSvg] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isRendering, setIsRendering] = useState(false)
  const [bindFunctions, setBindFunctions] = useState<BindFunctions>(undefined)
  const themeRef = useRef(theme)
  const renderSeqRef = useRef(0)

  useEffect(() => {
    themeRef.current = theme
    mermaid.initialize({
      startOnLoad: false,
      theme: theme as 'default',
      securityLevel: 'loose',
    })
  }, [theme])

  const render = useCallback(async (code: string, renderTheme?: MermaidTheme, options?: RenderOptions) => {
    const trimmed = code.trim()
    const seq = ++renderSeqRef.current

    if (!trimmed) {
      setSvg('')
      setError(null)
      setBindFunctions(undefined)
      return null
    }

    const securityLevel = options?.securityLevel ?? 'loose'
    const htmlLabels = options?.htmlLabels ?? true
    const isExportRender = options?.forExport ?? false

    if (!isExportRender) {
      setIsRendering(true)
    }
    try {
      const activeTheme = renderTheme ?? themeRef.current
      mermaid.initialize({
        startOnLoad: false,
        theme: activeTheme as 'default',
        securityLevel,
        htmlLabels,
      })
      const id = `mermaid-${crypto.randomUUID()}`
      const result = await mermaid.render(id, trimmed)

      if (!isExportRender) {
        if (seq !== renderSeqRef.current) {
          return null
        }
        setSvg(result.svg)
        setBindFunctions(() => result.bindFunctions)
        setError(null)
      }

      return result.svg
    } catch (err) {
      if (isExportRender) {
        throw err instanceof Error ? err : new Error('Failed to render diagram')
      }
      if (seq !== renderSeqRef.current) {
        return null
      }
      setSvg('')
      setBindFunctions(undefined)
      setError(err instanceof Error ? err.message : 'Failed to render diagram')
      return null
    } finally {
      if (!isExportRender && seq === renderSeqRef.current) {
        setIsRendering(false)
      }
    }
  }, [])

  return { svg, error, isRendering, bindFunctions, render }
}
