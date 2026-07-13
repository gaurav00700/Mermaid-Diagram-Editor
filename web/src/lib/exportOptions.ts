import exportOptions from '../../../src/mermaid_diagram/export_options.json'

export type MermaidTheme = (typeof exportOptions.themes)[number]
export type ExportFormat = 'png' | 'svg'

export interface ExportSettings {
  format: ExportFormat
  dpi: number
  background: string
  theme: MermaidTheme
  filename: string
}

export const EXPORT_OPTIONS = exportOptions

export const DEFAULT_EXPORT_SETTINGS: ExportSettings = {
  format: 'png',
  dpi: exportOptions.defaultDpi,
  background: exportOptions.defaultBackground,
  theme: exportOptions.defaultTheme as MermaidTheme,
  filename: 'diagram.png',
}
