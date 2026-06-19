import { useEffect, useState } from 'react'
import { BackgroundControl } from './BackgroundControl'
import {
  DEFAULT_EXPORT_SETTINGS,
  EXPORT_OPTIONS,
  type ExportSettings,
} from '../lib/exportOptions'

interface ExportDialogProps {
  open: boolean
  onClose: () => void
  onExport: (settings: ExportSettings) => void
  isExporting: boolean
  exportError: string | null
}

export function ExportDialog({
  open,
  onClose,
  onExport,
  isExporting,
  exportError,
}: ExportDialogProps) {
  const [settings, setSettings] = useState<ExportSettings>(DEFAULT_EXPORT_SETTINGS)

  useEffect(() => {
    if (!open) {
      return
    }
    setSettings(DEFAULT_EXPORT_SETTINGS)
  }, [open])

  if (!open) {
    return null
  }

  const updateFormat = (format: ExportSettings['format']) => {
    setSettings((current) => ({
      ...current,
      format,
      filename: format === 'svg' ? 'diagram.svg' : 'diagram.png',
    }))
  }

  return (
    <div className="dialog-backdrop" onClick={onClose}>
      <div className="dialog" onClick={(event) => event.stopPropagation()}>
        <div className="dialog-header">
          <h2>Export Diagram</h2>
          <button type="button" className="icon-button" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        <div className="dialog-body">
          <label>
            Format
            <select
              value={settings.format}
              onChange={(event) => updateFormat(event.target.value as ExportSettings['format'])}
            >
              <option value="png">PNG</option>
              <option value="svg">SVG</option>
            </select>
          </label>

          {settings.format === 'png' && (
            <label>
              DPI
              <div className="dpi-row">
                <select
                  value={EXPORT_OPTIONS.dpiPresets.includes(settings.dpi) ? settings.dpi : 'custom'}
                  onChange={(event) => {
                    const value = event.target.value
                    if (value !== 'custom') {
                      setSettings((current) => ({ ...current, dpi: Number(value) }))
                    }
                  }}
                >
                  {EXPORT_OPTIONS.dpiPresets.map((dpi) => (
                    <option key={dpi} value={dpi}>
                      {dpi}
                    </option>
                  ))}
                  <option value="custom">Custom</option>
                </select>
                <input
                  type="number"
                  min={72}
                  max={600}
                  value={settings.dpi}
                  onChange={(event) =>
                    setSettings((current) => ({
                      ...current,
                      dpi: Number(event.target.value) || current.dpi,
                    }))
                  }
                />
              </div>
            </label>
          )}

          <BackgroundControl
            value={settings.background}
            onChange={(background) => setSettings((current) => ({ ...current, background }))}
          />

          <label>
            Theme
            <select
              value={settings.theme}
              onChange={(event) =>
                setSettings((current) => ({
                  ...current,
                  theme: event.target.value as ExportSettings['theme'],
                }))
              }
            >
              {EXPORT_OPTIONS.themes.map((theme) => (
                <option key={theme} value={theme}>
                  {theme}
                </option>
              ))}
            </select>
          </label>

          <label>
            Filename
            <input
              type="text"
              value={settings.filename}
              onChange={(event) =>
                setSettings((current) => ({ ...current, filename: event.target.value }))
              }
            />
          </label>

          {exportError && <div className="dialog-error">{exportError}</div>}
        </div>

        <div className="dialog-footer">
          <button type="button" className="secondary" onClick={onClose}>
            Cancel
          </button>
          <button type="button" onClick={() => onExport(settings)} disabled={isExporting}>
            {isExporting ? 'Exporting…' : 'Download'}
          </button>
        </div>
      </div>
    </div>
  )
}
