# MCP Server

Expose Mermaid rendering as an MCP tool for Cursor, Claude, and other MCP clients. The tool returns inline PNG/SVG content and can optionally write to disk.

Repository: **https://github.com/gaurav00700/Mermaid-Diagram-Editor.git**

## Deployment modes

| Mode | Entry point | When to use |
|------|-------------|-------------|
| **uv (local)** | `uv run mermaid-diagram-mcp` | Dev machines with uv + Playwright |
| **Docker** | `docker compose --profile mcp run --rm -T mcp` | Isolated server with bundled Chromium |

Both modes use stdio transport and the same `render_mermaid_diagram` tool.

## Tool: `render_mermaid_diagram`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `code` | string | required | Mermaid source |
| `format` | `png` \| `svg` | `png` | Output format |
| `background` | string | `transparent` | `transparent`, `white`, or CSS color |
| `dpi` | int | `96` | PNG density base |
| `scale` | float | `1.0` | Extra PNG scale multiplier |
| `theme` | string | `default` | `default`, `dark`, `forest`, `neutral` |
| `output_path` | string | — | Optional file path to save output |

Example prompt in Cursor:

> Use the mermaid-diagram MCP tool to render this flowchart as a 300 DPI PNG with white background.

---

## Setup in this repository

### Prerequisites

**uv mode:**

```bash
uv sync
uv run playwright install chromium
```

**Docker mode:**

```bash
docker compose --profile mcp build mcp
```

### Cursor config (this repo)

The project includes [`.cursor/mcp.json`](../.cursor/mcp.json). Enable **one** server in **Cursor Settings → MCP**:

- `mermaid-diagram` — local uv server
- `mermaid-diagram-docker` — Docker compose server

When using Docker, set `output_path` under the mounted volume (e.g. `/output/diagram.png`). Compose maps `./output` on the host to `/output` in the container.

---

## Use from another project

Cursor does not support a raw `"git": "https://..."` field in `mcp.json`. You configure a **command** (stdio) or **url** (remote HTTP). To use this MCP server from a different workspace, add one of the configs below to that project's `.cursor/mcp.json` or global `~/.cursor/mcp.json`.

### Option A — `uvx` from Git (quickest)

```json
{
  "mcpServers": {
    "mermaid-diagram": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/gaurav00700/Mermaid-Diagram-Editor.git@main",
        "mermaid-diagram-mcp"
      ]
    }
  }
}
```

One-time on that machine:

```bash
uv run playwright install chromium
```

Pin a release tag instead of `@main` when available (e.g. `@v0.1.0`).

### Option B — Clone once + run (most stable)

One-time setup:

```bash
git clone https://github.com/gaurav00700/Mermaid-Diagram-Editor.git ~/.local/share/mcp/mermaid-diagram
cd ~/.local/share/mcp/mermaid-diagram
uv sync
uv run playwright install chromium
```

In the other project's `.cursor/mcp.json`:

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

Update later:

```bash
cd ~/.local/share/mcp/mermaid-diagram && git pull && uv sync
```

### Option C — Docker (no local Playwright)

One-time setup:

```bash
git clone https://github.com/gaurav00700/Mermaid-Diagram-Editor.git ~/.local/share/mcp/mermaid-diagram
cd ~/.local/share/mcp/mermaid-diagram
docker compose --profile mcp build mcp
```

In the other project:

```json
{
  "mcpServers": {
    "mermaid-diagram": {
      "command": "docker",
      "args": [
        "compose", "--profile", "mcp",
        "run", "--rm", "-T", "mcp"
      ],
      "cwd": "${userHome}/.local/share/mcp/mermaid-diagram"
    }
  }
}
```

Use `output_path` values like `/output/diagram.png` (written to `./output` in the clone directory).

### Option D — Global install (all Cursor projects)

```bash
uv tool install --from git+https://github.com/gaurav00700/Mermaid-Diagram-Editor.git mermaid-diagram
uv run playwright install chromium
```

Any `mcp.json`:

```json
{
  "mcpServers": {
    "mermaid-diagram": {
      "command": "mermaid-diagram-mcp",
      "args": []
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
| Daily dev with uv installed | **Option B** (clone + `cwd`) |
| Quick try in one project | **Option A** (`uvx`) |
| Avoid local Playwright setup | **Option C** (Docker) |
| Use across many projects | **Option D** (`uv tool install`) |

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
| Playwright browser missing | `uv run playwright install chromium` |
| Docker mode fails | `docker compose --profile mcp build mcp` in the clone directory |
| Asyncio / render error | Ensure latest `mcp_server.py` (render runs in a thread pool) |
| Duplicate tools | Enable only one of `mermaid-diagram` / `mermaid-diagram-docker` |
| `cwd: ${workspaceFolder}` in another project | Wrong — that only works when this repo is the open workspace |

---

## Related files

| File | Purpose |
|------|---------|
| [`src/mermaid_diagram/mcp_server.py`](../src/mermaid_diagram/mcp_server.py) | FastMCP server and tool |
| [`Dockerfile.mcp`](../Dockerfile.mcp) | Playwright-based MCP image |
| [`.cursor/mcp.json`](../.cursor/mcp.json) | Cursor config for this repo |
| [`export_options.json`](../export_options.json) | Shared defaults (themes, DPI) |
