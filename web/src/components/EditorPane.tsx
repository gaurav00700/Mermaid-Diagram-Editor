import { memo } from 'react'
import Editor from '@monaco-editor/react'
import type { editor } from 'monaco-editor'

interface EditorPaneProps {
  code: string
  onChange: (value: string) => void
  editorKey: number
}

const editorOptions: editor.IStandaloneEditorConstructionOptions = {
  minimap: { enabled: false },
  fontSize: 14,
  wordWrap: 'on',
  scrollBeyondLastLine: false,
  automaticLayout: true,
  tabSize: 2,
  padding: { top: 12 },
}

export const EditorPane = memo(function EditorPane({ code, onChange, editorKey }: EditorPaneProps) {
  return (
    <div className="editor-pane">
      <Editor
        key={editorKey}
        height="100%"
        path="diagram.mmd"
        defaultLanguage="markdown"
        theme="vs-dark"
        defaultValue={code}
        onChange={(value) => onChange(value ?? '')}
        options={editorOptions}
      />
    </div>
  )
})
