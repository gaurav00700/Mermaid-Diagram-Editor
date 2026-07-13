# MCP Server

Expose Mermaid rendering as an MCP tool for Cursor, Claude, and other MCP clients. The tool returns inline PNG/SVG content and can optionally write to disk.

Repository: **https://github.com/gaurav00700/Mermaid-Diagram-Editor.git**

## Deployment modes

| Mode | Entry point | When to use |
|------|-------------|-------------|
| **uv (local)** | `uv run mermaid-diagram-mcp` | Dev machines with uv + Playwright (stdio) |
| **Docker (HTTP)** | `docker compose --profile mcp up -d mcp` | Persistent server on port 8000 |

### Docker Compose services

[`docker-compose.yml`](../docker-compose.yml) defines:

| Service | Container name | Transport | Purpose |
|---------|----------------|-----------|---------|
| `web` | `mermaid-diagram-web` | HTTP (nginx) | Web app on port 8080 |
| `mcp` | `mermaid-diagram-mcp` | streamable-http | MCP on `http://localhost:8000/mcp` |

**Start Docker MCP:**

```bash
docker compose --profile mcp up -d --build mcp
```

Verify the server is listening (406 from plain curl is normal):

```bash
curl -i http://localhost:8000/mcp
```

Smoke test with MCP headers:

```bash
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"curl","version":"1.0"}}}'
```

Cursor config for Docker (requires `mcp` container running):

```json
{
  "mcpServers": {
    "mermaid-diagram-docker": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

Environment variables (used by `mcp_server.py`):

| Variable | Default | Values |
|----------|---------|--------|
| `MCP_TRANSPORT` | `stdio` | `stdio`, `streamable-http`, `sse` |
| `MCP_HOST` | `0.0.0.0` | Bind address (HTTP modes) |
| `MCP_PORT` | `8000` | Port (HTTP modes) |
| `MERMAID_WORKSPACE_ROOT` | — | Container path for relative `output_path` (Docker sets `/workspace`) |

Docker Compose volume env vars:

| Variable | Default | Mount |
|----------|---------|-------|
| `MERMAID_OUTPUT_DIR` | `./output` | `/output` (scratch exports in the server clone) |
| `MERMAID_WORKSPACE` | `./output` | `/workspace` (set to your client project for file save) |

Only `web` starts with `docker compose up`. MCP services use profile `mcp`.

## Tool: `render_mermaid_diagram`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `code` | string | required | Mermaid source |
| `format` | `png` \| `svg` | `png` | Output format |
| `background` | string | `transparent` | `transparent`, `white`, or CSS color |
| `dpi` | int | `96` | PNG density base |
| `scale` | float | `1.0` | Extra PNG scale multiplier |
| `theme` | string | `default` | `default`, `dark`, `forest`, `neutral` |
| `output_path` | string | — | Optional file path to save output. **uv/uvx:** use a project-relative path with `"cwd": "${workspaceFolder}"` (e.g. `docs/diagram.png`). **Docker:** same relative path with `MERMAID_WORKSPACE` set, or `/output/diagram.png`. |

Example prompt in Cursor:

> Use the mermaid-diagram MCP tool to render this flowchart as a 300 DPI PNG with white background.

---

## Setup in this repository

### Prerequisites

**uv mode** (local clone or dev — browsers auto-install on first render; pre-install optional):

```bash
uv sync
# optional: uv run playwright install chromium
```

**Docker mode:**

```bash
docker compose --profile mcp up -d --build mcp
```

### Cursor config (this repo)

The project includes [`.cursor/mcp.json`](../.cursor/mcp.json). Enable **one** server in **Cursor Settings → MCP**:

- `mermaid-diagram` — local uv server (stdio); [`mcp.json`](../.cursor/mcp.json) sets `"cwd": "${workspaceFolder}"` so relative `output_path` saves here
- `mermaid-diagram-docker` — Docker HTTP at `http://localhost:8000/mcp` (start `mcp` container first)

When using Docker in **this repo**, set `output_path` under the mounted volume (e.g. `/output/diagram.png` or `diagram.png`). Compose maps `./output` on the host to both `/output` and `/workspace` by default.

---

## Use from another project

Cursor does not support a raw `"git": "https://..."` field in `mcp.json`. You configure a **command** (stdio) or **url** (remote HTTP). To use this MCP server from a different workspace, add one of the configs below to that project's `.cursor/mcp.json` or global `~/.cursor/mcp.json`.

### Option A — `uvx` from Git (quickest)

Add to that project's `.cursor/mcp.json` or global `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "mermaid-diagram": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/gaurav00700/Mermaid-Diagram-Editor.git@main",
        "mermaid-diagram-mcp"
      ],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

**`cwd: "${workspaceFolder}"`** makes relative `output_path` values (e.g. `docs/diagram.png`) save into the project Cursor has open. No Docker volume mount needed.

Chromium is installed automatically on the **first render** if missing — no separate `playwright install` step. The first diagram may take longer while the browser downloads.

Pin a release tag instead of `@main` when available (e.g. `@v0.1.0`).

### Option B — Clone once + run (most stable)

One-time setup:

```bash
git clone https://github.com/gaurav00700/Mermaid-Diagram-Editor.git ~/.local/share/mcp/mermaid-diagram
cd ~/.local/share/mcp/mermaid-diagram
uv sync
```

Chromium auto-installs on first render. To pre-install: `uv run playwright install chromium`.

In the other project's `.cursor/mcp.json` (for saving into **that** project, add a second server or use Option A instead):

```json
{
  "mcpServers": {
    "mermaid-diagram": {
      "command": "uv",
      "args": ["run", "mermaid-diagram-mcp"],
      "cwd": "${userHome}/.local/share/mcp/mermaid-diagram"
    }
  }
}
```

`cwd` here points at the server clone (required for `uv run`). To save files into the **client** project, use Option A with `"cwd": "${workspaceFolder}"` or pass an absolute `output_path`.

Update later:

```bash
cd ~/.local/share/mcp/mermaid-diagram && git pull && uv sync
```

### Option C — Docker HTTP (no local Playwright)

One-time setup:

```bash
git clone https://github.com/gaurav00700/Mermaid-Diagram-Editor.git ~/.local/share/mcp/mermaid-diagram
cd ~/.local/share/mcp/mermaid-diagram
docker compose --profile mcp up -d --build mcp
```

**Save files into your client project** — mount that project as `/workspace` when starting the container:

```bash
cd ~/.local/share/mcp/mermaid-diagram
MERMAID_WORKSPACE=/path/to/your-project \
  docker compose --profile mcp up -d --build mcp
```

In the other project:

```json
{
  "mcpServers": {
    "mermaid-diagram-docker": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

Use `output_path` as a **project-relative** path (e.g. `docs/kg-build-pipeline.png`). That writes into your mounted project directory. Do **not** pass host absolute paths like `/Users/you/project/docs/diagram.png` — the container cannot see those unless they are bind-mounted.

Scratch exports without a workspace mount still work via `/output/diagram.png` (written to `./output` in the server clone directory).

### Option D — Global install (all Cursor projects)

```bash
uv tool install --from git+https://github.com/gaurav00700/Mermaid-Diagram-Editor.git mermaid-diagram
```

Chromium auto-installs on first render.

Any `mcp.json`:

```json
{
  "mcpServers": {
    "mermaid-diagram": {
      "command": "mermaid-diagram-mcp",
      "args": [],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

### Private repository

Use SSH or a token in the Git URL:

```text
git+ssh://git@github.com/gaurav00700/Mermaid-Diagram-Editor.git
```

Prefer SSH or a credential helper over committing tokens in config files.

---

## Which option to choose

| Situation | Recommended |
|-----------|-------------|
| Quick try in one project | **Option A** (`uvx` + `cwd`) |
| Daily dev with uv installed | **Option B** (clone + stable `cwd`) |
| Avoid local Playwright setup | **Option C** (Docker HTTP) |
| Use across many projects | **Option D** (`uv tool install` + `cwd`) |

---

## Verify

1. Save `.cursor/mcp.json` and reload MCP in Cursor Settings.
2. Confirm `mermaid-diagram` shows as connected.
3. Ask: *"Use render_mermaid_diagram to render a flowchart A → B as PNG."*

Run automated tests from the repo root:

```bash
uv run pytest tests/test_mcp.py -v
uv run pytest tests/ -m mcp_docker -v   # requires Docker
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Server not listed | Check `.cursor/mcp.json` path; reload MCP or restart Cursor |
| Playwright browser missing | Restart MCP and render again (auto-install runs on first render); or run `uv run playwright install chromium` manually |
| Docker mode fails | Run `docker compose --profile mcp up -d --build mcp` in the clone directory |
| `curl` returns 406 | Normal for plain GET — use MCP client or POST with `Accept: text/event-stream` |
| Asyncio / render error | Ensure latest `mcp_server.py` (render runs in a thread pool) |
| Duplicate tools | Enable only one of `mermaid-diagram` / `mermaid-diagram-docker` |
| `output_path` not created (uv/uvx) | Add `"cwd": "${workspaceFolder}"` and use a relative path like `docs/diagram.png` |
| `output_path` not created (Docker) | Start container with `MERMAID_WORKSPACE=/path/to/your-project`; use relative paths like `docs/diagram.png` |
| `output_path` host absolute path fails (Docker) | Use project-relative path or `/output/...` — host paths are not visible inside the container |

---

## Related files

| File | Purpose |
|------|---------|
| [`src/mermaid_diagram/mcp_server.py`](../src/mermaid_diagram/mcp_server.py) | FastMCP server and tool |
| [`Dockerfile.mcp`](../Dockerfile.mcp) | Playwright-based MCP image |
| [`docker-compose.yml`](../docker-compose.yml) | `web`, `mcp` (HTTP on port 8000) |
| [`.cursor/mcp.json`](../.cursor/mcp.json) | Cursor config for this repo |
| [`export_options.json`](../export_options.json) | Shared defaults (themes, DPI) |
