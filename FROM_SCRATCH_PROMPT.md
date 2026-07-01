# From-Scratch Prompt: Mermaid Diagram Editor

Use this prompt in Cursor Agent mode (or another AI coding agent) to recreate the full project from scratch.

---

## Prompt

Create a **Mermaid Diagram Editor** monorepo with three deployment modes that stay in sync:

1. **Web app** — React + Vite + TypeScript dev server
2. **Docker container** — nginx serving production build on port 8080
3. **Python CLI** — headless PNG/SVG rendering via Playwright + Typer, managed with **uv**

---

### Tech stack

**Web (`web/`):**

- React 19, TypeScript, Vite
- `@monaco-editor/react` + `monaco-editor` (bundle workers locally — do not use Monaco CDN workers)
- `mermaid` for live preview and export
- Dark theme UI with CSS variables
- Split-pane layout: resizable editor | preview

**Python (`src/mermaid_diagram/`):**

- Python 3.12+
- `uv` for dependency management (`pyproject.toml`, `uv.lock`)
- Typer CLI entry point: `mermaid-diagram`
- Playwright (Chromium) for CLI render/preview

**Infra:**

- Multi-stage `Dockerfile` (Node build → nginx serve)
- `docker-compose.yml` mapping `${PORT:-8080}:80`
- `nginx.conf` SPA fallback + no-cache headers for `index.html`

**Shared config:**

- Root `export_options.json` with themes, DPI presets, default theme/background/preview background
- Used by web export dialog, preview pane, and Python CLI

```json
{
  "themes": ["default", "dark", "forest", "neutral"],
  "dpiPresets": [72, 96, 150, 300],
  "defaultDpi": 96,
  "defaultTheme": "default",
  "defaultBackground": "transparent",
  "defaultPreviewBackground": "transparent"
}
```

---

### Web app features

**Editor pane:**

- Monaco editor for Mermaid source
- Use **`defaultValue`** + `editorKey` remount on upload/reset (not controlled `value` — required for live editing)
- Debounced preview render (~250 ms)

**Preview pane:**

- Live Mermaid SVG preview
- Call `bindFunctions` after injecting SVG (interactive diagrams)
- Pan (drag), zoom (buttons + mouse wheel with non-passive listener), reset view
- Preview background selector: transparent (checkerboard), white, custom hex — persist in `localStorage`
- Inject background rect into SVG when not transparent (WYSIWYG with export)

**Toolbar:**

- Upload `.mmd`, `.txt`, `.md`
- Reset to sample diagram
- Download → export dialog

**Export dialog:**

- Format: PNG or SVG
- PNG: DPI presets + custom value
- Background: transparent / white / custom hex
- Theme selector
- Filename input

**Export implementation:**

- PNG: re-render with `securityLevel: 'strict'` and `htmlLabels: false` (avoid tainted canvas + missing text)
- SVG: `loose` security + HTML labels
- Shared `injectBackground()` in `web/src/lib/background.ts`

**Persistence:**

- Save editor code to `localStorage`
- Default sample flowchart diagram

**Monaco setup:**

- `web/src/lib/monacoSetup.ts` bundles editor/JSON/CSS/HTML/TS workers via Vite
- Import from `main.tsx` before app render

---

### Python CLI

Commands via Typer:

```bash
uv run mermaid-diagram version
uv run mermaid-diagram render -i file.mmd -o out.png --dpi 300 --theme dark --background white
uv run mermaid-diagram render -i file.mmd -o out.svg -f svg
uv run mermaid-diagram preview -i file.mmd --background white --theme dark
```

**`render`:**

- Load Mermaid from jsDelivr CDN inside Playwright page
- PNG: screenshot with `omit_background` when transparent; scale = `dpi/96 * scale`
- SVG: inject background `<rect>` when not transparent
- Validate theme against `export_options.json`
- Exit code 1 on missing file, invalid syntax, unknown theme

**`preview`:**

- Headless=false browser with same render page; wait until browser closes
- CI tests validation only (invalid theme, missing file), not interactive preview

**Modules:**

- `cli.py`, `render.py`, `background.py`, `options.py`

---

### Project layout

```
mermaid_diagram/
├── export_options.json
├── pyproject.toml
├── uv.lock
├── AGENTS.md
├── README.md
├── Dockerfile
├── docker-compose.yml
├── nginx.conf
├── .dockerignore
├── .github/workflows/ci.yml
├── examples/sample.mmd
├── examples/invalid.mmd
├── src/mermaid_diagram/
├── web/
└── tests/
    ├── conftest.py
    ├── test_build.py
    ├── test_cli.py
    ├── test_web_local.py
    └── test_web_docker.py
```

---

### Testing (pytest + Playwright)

Three pytest markers: `cli`, `web_local`, `web_docker`

**CLI tests (~18):** version, SVG/PNG render, all themes, white background, DPI scaling, scale multiplier, default output path, error cases, preview validation

**Local web E2E (~12):** serve `web/dist` via Python HTTP server; test homepage, Monaco loads, preview renders, live edit, upload, reset, zoom controls/wheel/reset view, preview background, export dialog

**Docker E2E (~11):** `docker compose up -d --build`; curl health + static assets; same core Playwright tests on `localhost:8080`

**Test helpers (`tests/conftest.py`):**

- `compose_cmd()` — prefer `docker compose`, fallback `docker-compose`
- `run_cli()`, `local_web_server`, `docker_web_server` fixtures
- Shared Playwright assertions reused by local + docker suites
- Monaco editing: click `.monaco-editor`, use **`ControlOrMeta+A`** (not `Meta+A` — Linux CI breaks)

---

### CI (GitHub Actions)

On `pull_request` and push to `main`/`master`:

Three parallel jobs:

- `cli` → `pytest -m cli`
- `web-local` → `pytest -m web_local`
- `web-docker` → `pytest -m web_docker`

Each job: checkout, Node 20, `npm ci && npm run build`, `uv sync`, Playwright Chromium install

Fourth job `notify-success` (PR only): when all three pass, post/update PR comment via `peter-evans/create-or-update-comment@v4` listing CLI, local web, and container results

---

### Documentation

- **README.md** — setup, dev, CLI, Docker, testing, CI
- **AGENTS.md** — architecture, pitfalls, conventions for AI agents

---

### Important pitfalls to handle

| Issue | Fix |
|-------|-----|
| Monaco controlled value breaks typing | `defaultValue` + `editorKey` |
| PNG export blank/tainted | `strict` + `htmlLabels: false` for PNG |
| Docker stale UI | `--build` + nginx no-cache on `index.html` |
| Monaco workers fail offline | Bundle workers in Vite |
| Linux CI select-all fails | `ControlOrMeta+A` in Playwright |
| Wheel zoom not working | `{ passive: false }` on wheel listener |

---

### Deliverables

1. Working web app (`npm run dev` and `npm run build`)
2. Working CLI (`uv run mermaid-diagram render ...`)
3. Working Docker (`docker compose up --build` on :8080)
4. Full test suite passing locally
5. GitHub Actions CI with PR success comment
6. README + AGENTS.md

Build incrementally: scaffold → editor/preview → export → CLI → Docker → tests → CI.

---

## Short prompt (one paragraph)

Build a Mermaid diagram editor monorepo: React+Vite+Monaco+Mermaid web app with split-pane live preview (pan/zoom, preview background, PNG/SVG export), Python 3.12 CLI via uv+Typer+Playwright for headless render/preview, Docker+nginx production serve on :8080, shared `export_options.json`, pytest+Playwright tests for CLI/local web/Docker, and GitHub Actions CI with 3 parallel jobs + PR comment on success. Handle Monaco defaultValue, bundled workers, PNG strict export, and ControlOrMeta+A in E2E tests.
