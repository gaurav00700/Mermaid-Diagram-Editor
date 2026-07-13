from __future__ import annotations

import asyncio
import os
import warnings
from pathlib import Path
from typing import Literal

from fastmcp import FastMCP
from fastmcp.utilities.types import Image

from mermaid_diagram.options import get_themes, load_export_options
from mermaid_diagram.render import render_diagram_result

_defaults = load_export_options()

mcp = FastMCP(
    name="mermaid-diagram",
    instructions=(
        "Render Mermaid diagram source code to PNG or SVG. "
        "Use background, dpi, theme, and scale to match export preferences. "
        "For Docker HTTP mode, set output_path to a project-relative path "
        "(e.g. docs/diagram.png) when MERMAID_WORKSPACE mounts the client project "
        "to /workspace; host absolute paths are not writable inside the container."
    ),
)


def _validate_theme(theme: str) -> None:
    if theme not in get_themes():
        themes = ", ".join(get_themes())
        raise ValueError(f"Unknown theme '{theme}'. Choose from: {themes}")


def _resolve_output_path(output_path: str) -> Path:
    """Resolve output_path for local or containerized MCP.

    When MERMAID_WORKSPACE_ROOT is set (Docker), relative paths are written under
    that mount (e.g. docs/diagram.png -> /workspace/docs/diagram.png). Host
    absolute paths outside /output and /workspace raise a clear error.
    """
    path = Path(output_path)
    workspace_root = os.environ.get("MERMAID_WORKSPACE_ROOT")
    if not workspace_root:
        return path

    root = Path(workspace_root)
    if not path.is_absolute():
        return root / path

    normalized = path.as_posix()
    allowed_roots = {Path("/output").as_posix(), root.as_posix()}
    if not any(
        normalized == allowed or normalized.startswith(f"{allowed}/")
        for allowed in allowed_roots
    ):
        raise ValueError(
            f"output_path '{output_path}' is not writable in the Docker MCP container. "
            "Use a project-relative path (e.g. docs/diagram.png) after starting the container "
            "with MERMAID_WORKSPACE set to your project directory, or /output/diagram.png "
            "for the server clone's output folder."
        )
    return path


@mcp.tool()
async def render_mermaid_diagram(
    code: str,
    format: Literal["png", "svg"] = "png",
    background: str = _defaults["defaultBackground"],
    dpi: int = _defaults["defaultDpi"],
    scale: float = 1.0,
    theme: str = _defaults["defaultTheme"],
    output_path: str | None = None,
) -> list[Image | str]:
    """Render Mermaid source to PNG or SVG with configurable export options.

    Returns inline PNG image content or SVG text. When output_path is set,
    also writes the rendered file to that path. In Docker, use a path relative
    to the mounted workspace (e.g. docs/diagram.png) or /output/diagram.png.
    """
    _validate_theme(theme)

    try:
        result = await asyncio.to_thread(
            render_diagram_result,
            code,
            fmt=format,
            dpi=dpi,
            background=background,
            theme=theme,
            scale=scale,
        )
    except Exception as exc:
        raise ValueError(f"Render failed: {exc}") from exc

    saved_note = ""
    if output_path:
        path = _resolve_output_path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if format == "svg":
            if not isinstance(result, str):
                raise TypeError("Expected SVG string from render")
            path.write_text(result, encoding="utf-8")
        else:
            if not isinstance(result, bytes):
                raise TypeError("Expected PNG bytes from render")
            path.write_bytes(result)
        saved_note = f" Saved to {path}."

    if format == "svg":
        if not isinstance(result, str):
            raise TypeError("Expected SVG string from render")
        return [result, f"Rendered SVG ({theme} theme).{saved_note}"]

    if not isinstance(result, bytes):
        raise TypeError("Expected PNG bytes from render")
    return [
        Image(data=result, format="png"),
        f"Rendered PNG at {dpi} DPI with scale {scale} ({theme} theme).{saved_note}",
    ]


def main() -> None:
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="authlib")
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    run_kwargs: dict[str, object] = {"show_banner": False}
    if transport in {"streamable-http", "http", "sse"}:
        run_kwargs["host"] = os.environ.get("MCP_HOST", "0.0.0.0")
        run_kwargs["port"] = int(os.environ.get("MCP_PORT", "8000"))
    mcp.run(transport=transport, **run_kwargs)


if __name__ == "__main__":
    main()
