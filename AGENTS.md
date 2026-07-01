# AGENTS.md

Guidance for AI coding agents working on the **Mermaid Diagram Editor** repository.

## Project overview

Full-stack Mermaid diagram tool with three deployment modes that must stay in sync:

| Mode | Entry point | Purpose |
|------|-------------|---------|
| **Web (dev)** | `web/` → Vite dev server | Local React app with Monaco editor + live preview |
| **Web (container)** | `Dockerfile` + nginx | Production static build served on port 8080 |
| **CLI** | `src/mermaid_diagram/` | Headless PNG/SVG render and browser preview via Playwright |

Shared defaults (themes, DPI, backgrounds) live in [`export_options.json`](export_options.json) and are consumed by both the web app and Python CLI.

## Repository layout

```
export_options.json     # Shared themes/DPI/background defaults
pyproject.toml          # Python package + pytest config (uv)
src/mermaid_diagram/    # CLI: cli.py, render.py, background.py, history.py, options.py
web/                    # React 19 + Vite + TypeScript frontend
  src/
    App.tsx             # Shell: editor, preview, export, history sessions
    hooks/useHistory.ts # Session list, active session, create/switch/delete
    hooks/useMermaid.ts # Mermaid render + bindFunctions for interactivity
    lib/                # exportDiagram, background, history, downloadSource, exportOptions, monacoSetup
    components/         # EditorPane, PreviewPane, HistoryPanel, Toolbar, ExportDialog, …
tests/                  # pytest + Playwright (cli, web_local, web_docker)
examples/               # sample.mmd, invalid.mmd
.github/workflows/ci.yml
Dockerfile, docker-compose.yml, nginx.conf
```

## Commands agents should use

### Setup (once)

```bash
uv sync
uv run playwright install chromium
cd web && npm ci
```

### Development

```bash
cd web && npm run dev          # Vite dev server (~5173)
uv run mermaid-diagram render -i examples/sample.mmd -o out.png
docker compose up --build      # Container on :8080
```

### Build & test (run before finishing web/CLI changes)

```bash
cd web && npm run build
uv run pytest tests/ -v
uv run pytest tests/ -m cli -v
uv run pytest tests/ -m web_local -v
uv run pytest tests/ -m web_docker -v   # requires Docker
```

CI runs the three marked suites in parallel on every pull request (see [`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

## Architecture notes

### Web editor ↔ preview

- [`EditorPane.tsx`](web/src/components/EditorPane.tsx) uses Monaco **`defaultValue`** (not controlled `value`) so typing triggers `onChange` without fighting React state. Upload/reset bump `editorKey` to remount.
- [`App.tsx`](web/src/App.tsx) debounces preview renders by 250 ms via `useMermaid`.
- [`PreviewPane.tsx`](web/src/components/PreviewPane.tsx) injects SVG, calls `bindFunctions` for Mermaid click handlers, supports pan/zoom and preview background (persisted in `localStorage`).

### Export behavior

- **PNG export** re-renders with `securityLevel: 'strict'` and `htmlLabels: false` to avoid tainted canvas and missing text ([`App.tsx`](web/src/App.tsx) `handleExport`).
- **SVG export** uses `loose` security and HTML labels.
- Background injection is shared in [`web/src/lib/background.ts`](web/src/lib/background.ts) (web) and [`src/mermaid_diagram/background.py`](src/mermaid_diagram/background.py) (CLI).

### Monaco in Docker

- Workers are bundled locally in [`web/src/lib/monacoSetup.ts`](web/src/lib/monacoSetup.ts) (imported from `main.tsx`). Do not rely on Monaco CDN workers in production/Docker.

### CLI rendering

- [`render.py`](src/mermaid_diagram/render.py) loads Mermaid from jsDelivr CDN inside Playwright, renders to PNG (screenshot) or SVG (with optional background rect).
- `preview` command opens a headed browser; CI only tests validation paths, not interactive preview.
- [`history.py`](src/mermaid_diagram/history.py) stores sessions in `~/.local/share/mermaid-diagram/history.json` (override with `MERMAID_DIAGRAM_HISTORY_FILE` in tests).
- `source export` and `history export` write `.mmd` files (parity with web **Download**).

### Session history (web)

- Sessions stored in `localStorage` keys `mermaid-diagram-sessions` and `mermaid-diagram-active-session-id`.
- Legacy single-key draft `mermaid-diagram-code` is migrated on first load ([`web/src/lib/history.ts`](web/src/lib/history.ts)).
- [`useHistory`](web/src/hooks/useHistory.ts) drives active session; switching remounts Monaco via `editorKey`.
- **Download** (toolbar) saves source via [`downloadSource.ts`](web/src/lib/downloadSource.ts); **Export** opens PNG/SVG dialog.

## Shared config contract

When adding themes, DPI presets, or background defaults:

1. Update [`export_options.json`](export_options.json)
2. Web types flow from JSON via [`web/src/lib/exportOptions.ts`](web/src/lib/exportOptions.ts)
3. Python reads via [`src/mermaid_diagram/options.py`](src/mermaid_diagram/options.py)
4. Extend CLI theme validation and export/preview UI as needed
5. Add/adjust tests in `tests/test_cli.py` and web E2E helpers in `tests/conftest.py`

## Testing conventions

- **Fixtures & helpers**: [`tests/conftest.py`](tests/conftest.py) — `run_cli`, `compose_cmd`, `local_web_server`, `docker_web_server`, shared Playwright assertions.
- **Markers**: `cli`, `web_local`, `web_docker` (registered in `pyproject.toml`).
- **Monaco E2E**: use `_set_monaco_content()` in conftest — clicks `.monaco-editor`, **`ControlOrMeta+A`** (not `Meta+A`; Linux CI uses Ctrl), then types. Never click hidden Monaco textareas (overlay intercepts).
- **Docker**: prefer `docker compose` with fallback to `docker-compose` via `compose_cmd()`.
- **New web UI features**: add assertions to conftest helpers and cover in both `test_web_local.py` and `test_web_docker.py` when behavior should match in container.

## Coding standards

### General

- Keep changes minimal and scoped to the task.
- Match existing naming, file layout, and patterns.
- Do not commit secrets, `.env` files, or generated `web/dist/` output.
- Only create git commits when explicitly asked.

### TypeScript / React (`web/`)

- Functional components; hooks for reusable logic.
- CSS in [`web/src/styles/app.css`](web/src/styles/app.css) with existing CSS variables (`--surface`, `--accent`, etc.).
- Import shared background/export logic from `web/src/lib/`, not duplicated inline.

### Python (`src/mermaid_diagram/`)

- Python 3.12+, type hints, `from __future__ import annotations` where used.
- CLI via Typer; surface user-facing errors with `typer.secho` and exit code 1.
- Run CLI/tests through **`uv run`**, not bare `python`.

## Common pitfalls

| Pitfall | Correct approach |
|---------|------------------|
| Controlled Monaco `value` breaks live edit | Use `defaultValue` + `editorKey` remount |
| PNG export blank / tainted canvas | Export render with `strict` + `htmlLabels: false` |
| Docker shows old UI | `docker compose up --build` + hard refresh |
| `docker-compose` missing on CI | Use `compose_cmd()` helper |
| Playwright select-all fails on Linux | `ControlOrMeta+A`, not `Meta+A` |
| Stale nginx `index.html` cache | `nginx.conf` no-cache for `index.html`; rebuild image |

## CI expectations

Pull requests trigger three jobs (`cli`, `web-local`, `web-docker`). All must pass. On success, a bot comment is posted on the PR (no secrets required).

When changing tests or workflow, verify locally with the same pytest markers CI uses.

## Out of scope unless requested

- Slack/email notifications
- Interactive `preview` command testing in CI
- Branch protection or GitHub repo settings
- Large refactors unrelated to the task

## Reference

Human-oriented setup and usage: [`README.md`](README.md).
