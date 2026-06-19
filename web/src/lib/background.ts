import type { CSSProperties } from 'react'
import { EXPORT_OPTIONS } from './exportOptions'

export const PREVIEW_BACKGROUND_STORAGE_KEY = 'mermaid-diagram-preview-background'

export const CHECKERBOARD_BACKGROUND =
  'radial-gradient(circle at 1px 1px, rgba(255, 255, 255, 0.05) 1px, transparent 0), var(--surface)'

export type BackgroundPreset = 'transparent' | 'white' | 'custom'

export function resolveBackgroundColor(background: string): string | null {
  if (background === 'transparent') {
    return null
  }
  if (background === 'white') {
    return '#ffffff'
  }
  return background
}

export function previewViewportStyle(background: string): CSSProperties {
  const color = resolveBackgroundColor(background)
  if (color === null) {
    return {
      background: CHECKERBOARD_BACKGROUND,
      backgroundSize: '16px 16px',
    }
  }
  return { background: color }
}

export function backgroundPresetValue(background: string): BackgroundPreset {
  if (background === 'transparent' || background === 'white') {
    return background
  }
  return 'custom'
}

export function loadPreviewBackground(): string {
  const saved = localStorage.getItem(PREVIEW_BACKGROUND_STORAGE_KEY)
  return saved ?? EXPORT_OPTIONS.defaultPreviewBackground
}

export function injectBackground(svg: string, background: string): string {
  if (background === 'transparent') {
    return svg
  }

  const color = resolveBackgroundColor(background)
  if (!color) {
    return svg
  }

  const insertAt = svg.indexOf('>')
  if (insertAt === -1) {
    return svg
  }

  return `${svg.slice(0, insertAt + 1)}<rect width="100%" height="100%" fill="${color}"/>${svg.slice(insertAt + 1)}`
}
