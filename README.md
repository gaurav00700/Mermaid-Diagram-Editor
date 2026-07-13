# Mermaid Diagram Editor

A split-pane Mermaid editor with live preview, browser export (PNG/SVG), a Python CLI via [uv](https://docs.astral.sh/uv/), and Docker-based production serving.

## Features

- Monaco editor with live preview
- Upload `.mmd`, `.txt`, or `.md` files from your computer
- Preview background: transparent (checkerboard), white, or custom hex
- Export PNG or SVG with custom DPI, background, and theme
- **Download** Mermaid source (`.mmd`) from the toolbar
- **History** panel: create new diagram sessions, switch between previous sessions, rename/delete
- Persist sessions in `localStorage` (web/Docker)
- CLI for headless batch rendering and file-based session history
- **MCP server** for AI assistants (Cursor/Claude) — render diagrams via tool call ([guide](docs/mcp-server.md))
- Docker image for serving the built web app with nginx

## Documentation

| Guide | Description |
|-------|-------------|
| [MCP Server](docs/mcp-server.md) | Cursor MCP setup, tool reference, using the server from other projects via Git, troubleshooting |

## Prerequisites

- [uv](https://docs.astral.sh/uv/) for the Python CLI
- Node.js 20+ for local web development
- Docker (optional) for containerized serving

## Local setup

```bash
# Install Python CLI dependencies
uv sync

# Install Playwright browser (one-time, for CLI)
uv run playwright install chromium

# Install web dependencies
cd web && npm install
```

## Web app (development)

```bash
cd web
npm run dev
```

Open the URL shown in the terminal (typically `http://localhost:5173`).

### Toolbar actions

| Button | Action |
|--------|--------|
| **History** | Open session list — switch diagrams, create new, rename, delete |
| **Upload** | Load `.mmd`, `.txt`, or `.md` into the active session |
| **Download** | Save current Mermaid source as `.mmd` |
| **Export** | Export rendered diagram as PNG or SVG |
| **Reset** | Restore the default sample diagram in the active session |

## CLI

```bash
# Render to PNG at 300 DPI
uv run mermaid-diagram render -i examples/sample.mmd -o diagram.png --dpi 300

# Render to SVG with theme and background
uv run mermaid-diagram render -i examples/sample.mmd -o diagram.svg -f svg --theme dark --background white

# Open an interactive browser preview with background
uv run mermaid-diagram preview -i examples/sample.mmd --background white --theme dark

# Download / copy Mermaid source to a .mmd file
uv run mermaid-diagram source export -i examples/sample.mmd -o diagram.mmd

# Session history (stored in ~/.local/share/mermaid-diagram/history.json)
uv run mermaid-diagram history save -i examples/sample.mmd --title "Sample"
uv run mermaid-diagram history list
uv run mermaid-diagram history show <session-id>
uv run mermaid-diagram history export <session-id> -o restored.mmd
uv run mermaid-diagram history new --title "Fresh diagram"
uv run mermaid-diagram history delete <session-id>

# Optional editable install
uv tool install -e .
mermaid-diagram render -i examples/sample.mmd -o out.png
```

### CLI options

| Flag | Description |
|------|-------------|
| `-i, --input` | Input `.mmd`, `.txt`, or `.md` file (required) |
| `-o, --output` | Output file path |
| `-f, --format` | `png` or `svg` |
| `--dpi` | PNG scale base (`scale = dpi / 96`, default 96) |
| `-b, --background` | `transparent`, `white`, or `#hex` |
| `-t, --theme` | Mermaid theme: `default`, `dark`, `forest`, `neutral` |
| `-s, --scale` | Extra scale multiplier |

### CLI preview

| Flag | Description |
|------|-------------|
| `-i, --input` | Input `.mmd`, `.txt`, or `.md` file (required) |
| `-b, --background` | Preview background: `transparent`, `white`, or `#hex` |
| `-t, --theme` | Mermaid theme |

Close the browser window to exit preview mode.

### CLI history and source

| Command | Description |
|---------|-------------|
| `source export -i … -o …` | Write Mermaid source to a `.mmd` file |
| `history save -i … [--title]` | Save a file as a history session |
| `history list` | List saved sessions |
| `history show <id>` | Print session source to stdout |
| `history export <id> -o …` | Write session source to a `.mmd` file |
| `history new [--title]` | Create a session from the default sample |
| `history delete <id>` | Remove a saved session |

## MCP Server

See [docs/mcp-server.md](docs/mcp-server.md) for setup, tool parameters, and using the server from other projects.

Quick start in this repo:

```bash
uv sync && uv run playwright install chromium
```

Enable `mermaid-diagram` or `mermaid-diagram-docker` from [`.cursor/mcp.json`](.cursor/mcp.json) in Cursor Settings → MCP.

## Docker serve

Run the production build without installing Node locally:

```bash
docker compose up --build
```

Open `http://localhost:8080`. After pulling or changing code, rebuild with `--build` and hard-refresh the browser (Cmd+Shift+R) so you get the latest assets.

Override the host port:

```bash
PORT=3000 docker compose up --build
```

Build and run the image directly:

```bash
docker build -t mermaid-diagram:latest .
docker run -p 8080:80 mermaid-diagram:latest
```

## Shared export settings

Themes, DPI presets, preview/export background defaults, and history limits live in [`export_options.json`](export_options.json) and are used by the web app, export dialog, and Python CLI.

## Project layout

```
mermaid_diagram/
├── export_options.json
├── pyproject.toml
├── Dockerfile
├── Dockerfile.mcp
├── docker-compose.yml
├── .cursor/mcp.json
├── examples/
├── docs/                  # Documentation (see docs/mcp-server.md)
├── src/mermaid_diagram/   # Python CLI + MCP server
└── web/                   # React + Vite app
```

## Build web for production

```bash
cd web
npm run build
```

Static output is written to `web/dist/`.

## Testing

Install dev dependencies and Playwright once:

```bash
uv sync
uv run playwright install chromium
cd web && npm ci && npm run build
```

Run the full suite:

```bash
uv run pytest tests/ -v
```

Run each mode separately:

```bash
uv run pytest tests/ -m cli -v          # CLI + MCP (uv) render validation
uv run pytest tests/ -m web_local -v    # E2E against locally served web/dist
uv run pytest tests/ -m web_docker -v   # E2E against docker compose (requires Docker)
uv run pytest tests/test_mcp.py -v      # MCP tool tests only
uv run pytest tests/ -m mcp_docker -v   # MCP Docker container tests
```

| Suite | Marker | What it covers |
|-------|--------|----------------|
| CLI | `cli` | PNG/SVG render, themes, backgrounds, DPI, scale, error handling, MCP tool (uv) |
| Local web | `web_local` | Editor, preview, upload, zoom, background, export dialog |
| Container | `web_docker` | `docker compose up --build` + same E2E on `localhost:8080` |
| MCP (Docker) | `mcp_docker` | MCP image build, container render, output volume |

## CI

GitHub Actions runs four parallel jobs on every pull request (see [`.github/workflows/ci.yml`](.github/workflows/ci.yml)):

- **CLI tests** — `pytest -m cli` (includes MCP uv tests)
- **Local web tests** — `pytest -m web_local`
- **Container web tests** — `pytest -m web_docker`
- **MCP Docker tests** — `pytest -m mcp_docker`

When all jobs pass, a comment is posted on the pull request summarizing the results. Failed runs do not post a success comment.
