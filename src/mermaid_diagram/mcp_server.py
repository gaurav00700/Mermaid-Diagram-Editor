from __future__ import annotations

import asyncio
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
        "Use background, dpi, theme, and scale to match export preferences."
    ),
)


def _validate_theme(theme: str) -> None:
    if theme not in get_themes():
        themes = ", ".join(get_themes())
        raise ValueError(f"Unknown theme '{theme}'. Choose from: {themes}")


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
    also writes the rendered file to that path.
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
        path = Path(output_path)
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
    mcp.run()


if __name__ == "__main__":
    main()
