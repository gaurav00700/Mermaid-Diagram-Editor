# Mermaid Diagram Editor

A split-pane Mermaid editor with live preview, browser export (PNG/SVG), a Python CLI via [uv](https://docs.astral.sh/uv/), and Docker-based production serving.

## Features

- Monaco editor with live preview
- Upload `.mmd`, `.txt`, or `.md` files from your computer
- Preview background: transparent (checkerboard), white, or custom hex
- Export PNG or SVG with custom DPI, background, and theme
- Persist editor content in `localStorage`
- CLI for headless batch rendering
- Docker image for serving the built web app with nginx

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

## CLI

```bash
# Render to PNG at 300 DPI
uv run mermaid-diagram render -i examples/sample.mmd -o diagram.png --dpi 300

# Render to SVG with theme and background
uv run mermaid-diagram render -i examples/sample.mmd -o diagram.svg -f svg --theme dark --background white

# Open an interactive browser preview with background
uv run mermaid-diagram preview -i examples/sample.mmd --background white --theme dark

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

Themes, DPI presets, preview/export background defaults live in [`export_options.json`](export_options.json) and are used by the web app, export dialog, and Python CLI.

## Project layout

```
mermaid_diagram/
├── export_options.json
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── examples/
├── src/mermaid_diagram/   # Python CLI
└── web/                   # React + Vite app
```

## Build web for production

```bash
cd web
npm run build
```

Static output is written to `web/dist/`.
