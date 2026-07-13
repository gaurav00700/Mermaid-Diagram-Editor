"""MCP server tests for mermaid-diagram render tool (uv/local)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from fastmcp.utilities.types import Image

from conftest import (
    INVALID,
    SAMPLE,
    invoke_render_mermaid_diagram,
    png_bytes_dimensions,
    png_dimensions,
    run_cli,
)
from mermaid_diagram.render import render_diagram_result

pytestmark = pytest.mark.cli

SAMPLE_CODE = SAMPLE.read_text(encoding="utf-8")
INVALID_CODE = INVALID.read_text(encoding="utf-8")


def test_render_diagram_result_png() -> None:
    result = render_diagram_result(SAMPLE_CODE, fmt="png")
    assert isinstance(result, bytes)
    assert result[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(result) > 0


def test_render_diagram_result_svg() -> None:
    result = render_diagram_result(SAMPLE_CODE, fmt="svg")
    assert isinstance(result, str)
    assert result.startswith("<svg")
    ET.fromstring(result)


def test_mcp_tool_render_png_default() -> None:
    result = invoke_render_mermaid_diagram(code=SAMPLE_CODE, format="png")
    assert len(result) == 2
    assert isinstance(result[0], Image)
    assert isinstance(result[0].data, bytes)
    assert result[0].data[:8] == b"\x89PNG\r\n\x1a\n"
    assert "Rendered PNG" in result[1]


def test_mcp_tool_render_svg() -> None:
    result = invoke_render_mermaid_diagram(code=SAMPLE_CODE, format="svg")
    assert len(result) == 2
    assert isinstance(result[0], str)
    assert result[0].startswith("<svg")
    assert "Rendered SVG" in result[1]


def test_mcp_tool_png_dpi_scaling() -> None:
    low = invoke_render_mermaid_diagram(code=SAMPLE_CODE, format="png", dpi=96)
    high = invoke_render_mermaid_diagram(code=SAMPLE_CODE, format="png", dpi=300)
    low_w, _ = png_bytes_dimensions(low[0].data)
    high_w, _ = png_bytes_dimensions(high[0].data)
    assert high_w > low_w
    assert high_w / low_w == pytest.approx(300 / 96, rel=0.05)


def test_mcp_tool_png_scale() -> None:
    base = invoke_render_mermaid_diagram(code=SAMPLE_CODE, format="png", dpi=96, scale=1.0)
    scaled = invoke_render_mermaid_diagram(code=SAMPLE_CODE, format="png", dpi=96, scale=2.0)
    base_w, _ = png_bytes_dimensions(base[0].data)
    scaled_w, _ = png_bytes_dimensions(scaled[0].data)
    assert scaled_w > base_w
    assert scaled_w / base_w == pytest.approx(2.0, rel=0.05)


def test_mcp_tool_svg_background_white() -> None:
    result = invoke_render_mermaid_diagram(
        code=SAMPLE_CODE,
        format="svg",
        background="white",
    )
    svg = result[0]
    assert isinstance(svg, str)
    assert 'fill="#ffffff"' in svg or "fill='#ffffff'" in svg


def test_mcp_tool_png_background_white() -> None:
    result = invoke_render_mermaid_diagram(
        code=SAMPLE_CODE,
        format="png",
        background="white",
    )
    assert isinstance(result[0], Image)
    assert len(result[0].data) > 0


@pytest.mark.parametrize("theme", ["default", "dark", "forest", "neutral"])
def test_mcp_tool_all_themes(theme: str) -> None:
    result = invoke_render_mermaid_diagram(code=SAMPLE_CODE, format="png", theme=theme)
    assert isinstance(result[0], Image)
    assert len(result[0].data) > 0


def test_mcp_tool_output_path_png(tmp_path: Path) -> None:
    output = tmp_path / "diagram.png"
    result = invoke_render_mermaid_diagram(
        code=SAMPLE_CODE,
        format="png",
        output_path=str(output),
    )
    assert output.exists()
    assert output.read_bytes() == result[0].data
    assert "Saved to" in result[1]


def test_mcp_tool_output_path_svg(tmp_path: Path) -> None:
    output = tmp_path / "diagram.svg"
    result = invoke_render_mermaid_diagram(
        code=SAMPLE_CODE,
        format="svg",
        output_path=str(output),
    )
    svg = result[0]
    assert isinstance(svg, str)
    assert output.read_text(encoding="utf-8") == svg
    assert "Saved to" in result[1]


def test_mcp_tool_invalid_theme() -> None:
    with pytest.raises(ValueError, match="Unknown theme"):
        invoke_render_mermaid_diagram(code=SAMPLE_CODE, format="png", theme="unknown")


def test_mcp_tool_invalid_syntax() -> None:
    with pytest.raises(ValueError, match="Render failed"):
        invoke_render_mermaid_diagram(code=INVALID_CODE, format="png")


def test_render_diagram_still_writes_file(tmp_path: Path) -> None:
    output = tmp_path / "cli-out.png"
    result = run_cli("render", "-i", str(SAMPLE), "-o", str(output))
    assert result.returncode == 0, result.stderr
    assert output.exists()
    low_w, _ = png_dimensions(output)
    assert low_w > 0


def test_mcp_stdio_tool_call() -> None:
    import asyncio

    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    from conftest import ROOT

    async def _run() -> None:
        params = StdioServerParameters(
            command="uv",
            args=["run", "mermaid-diagram-mcp"],
            cwd=str(ROOT),
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                assert any(tool.name == "render_mermaid_diagram" for tool in tools.tools)
                result = await session.call_tool(
                    "render_mermaid_diagram",
                    {"code": SAMPLE_CODE, "format": "png"},
                )
                assert not result.isError
                assert any(block.type == "image" for block in result.content)

    asyncio.run(_run())
