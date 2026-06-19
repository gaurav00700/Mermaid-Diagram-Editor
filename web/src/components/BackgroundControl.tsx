import { backgroundPresetValue } from '../lib/background'

interface BackgroundControlProps {
  value: string
  onChange: (background: string) => void
  className?: string
}

export function BackgroundControl({ value, onChange, className }: BackgroundControlProps) {
  const preset = backgroundPresetValue(value)

  return (
    <div className={className ?? 'background-control'}>
      <label className="background-control-label">
        <span>Background</span>
        <select
          value={preset}
          onChange={(event) => {
            const next = event.target.value
            onChange(next === 'custom' ? '#ffffff' : next)
          }}
        >
          <option value="transparent">Transparent</option>
          <option value="white">White</option>
          <option value="custom">Custom hex</option>
        </select>
      </label>
      {preset === 'custom' && (
        <label className="background-control-label">
          <span>Color</span>
          <input
            type="color"
            value={value.startsWith('#') ? value : '#ffffff'}
            onChange={(event) => onChange(event.target.value)}
          />
        </label>
      )}
    </div>
  )
}
