export const DEFAULT_DIAGRAM = `flowchart TD
    A[Start] --> B{Is it working?}
    B -->|Yes| C[Great!]
    B -->|No| D[Debug]
    D --> B
`

export const STORAGE_KEY = 'mermaid-diagram-code'
