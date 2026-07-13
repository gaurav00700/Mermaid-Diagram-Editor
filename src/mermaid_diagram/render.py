from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from mermaid_diagram.background import background_css, inject_svg_background

MERMAID_VERSION = "11.15.0"
MERMAID_CDN = f"https://cdn.jsdelivr.net/npm/mermaid@{MERMAID_VERSION}/dist/mermaid.min.js"
_playwright_ready = False
_CHROMIUM_DOCKER_ARGS = (
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
)


def _running_in_container() -> bool:
    return Path("/.dockerenv").is_file() or os.environ.get("MERMAID_CHROMIUM_NO_SANDBOX") == "1"


def _chromium_launch_kwargs(*, headless: bool) -> dict[str, object]:
    kwargs: dict[str, object] = {"headless": headless}
    if _running_in_container():
        kwargs["args"] = list(_CHROMIUM_DOCKER_ARGS)
    return kwargs


def _launch_chromium(playwright: object, *, headless: bool = True):
    launch = getattr(getattr(playwright, "chromium"), "launch")
    return launch(**_chromium_launch_kwargs(headless=headless))

RENDER_PAGE = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    html, body {{
      margin: 0;
      padding: 16px;
      background: {background_css};
    }}
    #container {{
      display: inline-block;
    }}
  </style>
</head>
<body>
  <div id="container"></div>
  <script src="{mermaid_cdn}"></script>
  <script>
    const code = {code_json};
    const theme = {theme_json};

    mermaid.initialize({{
      startOnLoad: false,
      theme,
      securityLevel: "strict",
    }});

    async function renderDiagram() {{
      const {{ svg }} = await mermaid.render("export-diagram", code);
      document.getElementById("container").innerHTML = svg;
      return svg;
    }}

    window.__renderDiagram = renderDiagram;
  </script>
</body>
</html>
"""


def _infer_format(output: Path, fmt: str | None) -> str:
    if fmt:
        return fmt.lower()
    suffix = output.suffix.lower().lstrip(".")
    if suffix in {"png", "svg"}:
        return suffix
    return "png"


def _build_page_html(code: str, background: str, theme: str) -> str:
    return RENDER_PAGE.format(
        background_css=background_css(background),
        mermaid_cdn=MERMAID_CDN,
        code_json=json.dumps(code),
        theme_json=json.dumps(theme),
    )


def _ensure_playwright_chromium() -> None:
    """Install Chromium on first use when missing (uvx / fresh installs)."""
    global _playwright_ready
    if _playwright_ready or os.environ.get("MERMAID_SKIP_PLAYWRIGHT_INSTALL"):
        return

    try:
        with sync_playwright() as playwright:
            browser = _launch_chromium(playwright)
            browser.close()
    except Exception:
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
        )
    _playwright_ready = True


def render_diagram_result(
    code: str,
    *,
    fmt: str = "png",
    dpi: int = 96,
    background: str = "transparent",
    theme: str = "default",
    scale: float = 1.0,
) -> bytes | str:
    """Render Mermaid source to PNG bytes or an SVG string."""
    output_format = fmt.lower()
    if output_format not in {"png", "svg"}:
        raise ValueError(f"Unsupported format: {output_format}")

    _ensure_playwright_chromium()

    page_html = _build_page_html(code, background, theme)
    device_scale = (dpi / 96.0) * scale

    with sync_playwright() as playwright:
        browser = _launch_chromium(playwright)
        context = browser.new_context(device_scale_factor=device_scale)
        page = context.new_page()

        page.set_content(page_html, wait_until="networkidle")
        svg = page.evaluate("() => window.__renderDiagram()")

        if output_format == "svg":
            if background not in {"transparent", ""}:
                svg = inject_svg_background(svg, background_css(background))
            result: bytes | str = svg
        else:
            container = page.locator("#container")
            container.wait_for(state="visible")
            result = container.screenshot(type="png", omit_background=background == "transparent")

        context.close()
        browser.close()

    return result


def render_diagram(
    code: str,
    output: Path,
    *,
    fmt: str | None = None,
    dpi: int = 96,
    background: str = "transparent",
    theme: str = "default",
    scale: float = 1.0,
) -> None:
    output_format = _infer_format(output, fmt)
    result = render_diagram_result(
        code,
        fmt=output_format,
        dpi=dpi,
        background=background,
        theme=theme,
        scale=scale,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "svg":
        if not isinstance(result, str):
            raise TypeError("Expected SVG string from render_diagram_result")
        output.write_text(result, encoding="utf-8")
    else:
        if not isinstance(result, bytes):
            raise TypeError("Expected PNG bytes from render_diagram_result")
        output.write_bytes(result)


def preview_diagram(
    code: str,
    *,
    background: str = "transparent",
    theme: str = "default",
) -> None:
    page_html = _build_page_html(code, background, theme)

    with sync_playwright() as playwright:
        browser = _launch_chromium(playwright, headless=False)
        page = browser.new_page(viewport={"width": 1200, "height": 800})
        page.set_content(page_html, wait_until="networkidle")
        page.evaluate("() => window.__renderDiagram()")

        while browser.is_connected():
            page.wait_for_timeout(500)

        browser.close()
