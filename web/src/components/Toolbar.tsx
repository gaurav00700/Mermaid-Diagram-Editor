import { useRef } from 'react'

interface ToolbarProps {
  onUpload: (content: string) => void
  onDownload: () => void
  onReset: () => void
  uploadError: string | null
}

export function Toolbar({ onUpload, onDownload, onReset, uploadError }: ToolbarProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) {
      return
    }

    const reader = new FileReader()
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        onUpload(reader.result)
      }
    }
    reader.onerror = () => {
      onUpload('')
    }
    reader.readAsText(file)
    event.target.value = ''
  }

  return (
    <header className="toolbar">
      <div className="toolbar-left">
        <h1>Mermaid Editor</h1>
        {uploadError && <span className="toolbar-error">{uploadError}</span>}
      </div>
      <div className="toolbar-actions">
        <input
          ref={fileInputRef}
          type="file"
          accept=".mmd,.txt,.md,text/plain"
          hidden
          onChange={handleFileChange}
        />
        <button type="button" onClick={() => fileInputRef.current?.click()}>
          Upload
        </button>
        <button type="button" onClick={onDownload}>
          Download
        </button>
        <button type="button" className="secondary" onClick={onReset}>
          Reset
        </button>
      </div>
    </header>
  )
}
