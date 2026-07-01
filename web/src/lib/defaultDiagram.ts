export const DEFAULT_DIAGRAM = `flowchart TD
    A[Start] --> B{Is it working?}
    B -->|Yes| C[Great!]
    B -->|No| D[Debug]
    D --> B
`

export const LEGACY_STORAGE_KEY = 'mermaid-diagram-code'
/** @deprecated Use session storage via history.ts */
export const STORAGE_KEY = LEGACY_STORAGE_KEY
