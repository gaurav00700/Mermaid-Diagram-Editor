"""Docker MCP server tests for mermaid-diagram."""

from __future__ import annotations

import base64
import subprocess
import textwrap
from pathlib import Path

import pytest

from conftest import INVALID, ROOT, SAMPLE, compose_cmd, ensure_mcp_image_built, run_mcp_docker

pytestmark = pytest.mark.mcp_docker


def _docker_available() -> bool:
    return compose_cmd() is not None


@pytest.fixture(scope="module", autouse=True)
def _build_mcp_image() -> None:
    if not _docker_available():
        pytest.skip("Docker Compose is not available")
    ensure_mcp_image_built()


def _run_render_in_container(
    *,
    code: str,
    fmt: str = "png",
    theme: str = "default",
    background: str = "transparent",
    output_path: str | None = None,
) -> subprocess.CompletedProcess[str]:
    output_path_literal = "None" if output_path is None else repr(output_path)
    script = textwrap.dedent(
        f"""
        from pathlib import Path
        from mermaid_diagram.render import render_diagram_result
        code = {code!r}
        result = render_diagram_result(
            code,
            fmt={fmt!r},
            theme={theme!r},
            background={background!r},
        )
        if {fmt!r} == "png":
            import base64
            print(base64.b64encode(result).decode("ascii"))
        else:
            print(result)
        if {output_path_literal} is not None:
            path = Path({output_path_literal})
            path.parent.mkdir(parents=True, exist_ok=True)
            if {fmt!r} == "png":
                path.write_bytes(result)
            else:
                path.write_text(result, encoding="utf-8")
        """
    ).strip()
    return run_mcp_docker("uv", "run", "python", "-c", script)


def test_mcp_docker_image_builds() -> None:
    assert _docker_available()
    ensure_mcp_image_built()


def test_mcp_docker_render_png() -> None:
    code = SAMPLE.read_text(encoding="utf-8")
    result = _run_render_in_container(code=code, fmt="png")
    assert result.returncode == 0, result.stderr
    png_data = base64.b64decode(result.stdout.strip())
    assert png_data[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(png_data) > 0


def test_mcp_docker_render_svg() -> None:
    code = SAMPLE.read_text(encoding="utf-8")
    result = _run_render_in_container(code=code, fmt="svg")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().startswith("<svg")


def test_mcp_docker_output_volume() -> None:
    host_output = ROOT / "output"
    host_output.mkdir(exist_ok=True)
    for existing in host_output.glob("diagram.png"):
        existing.unlink()

    code = SAMPLE.read_text(encoding="utf-8")
    result = _run_render_in_container(
        code=code,
        fmt="png",
        output_path="/output/diagram.png",
    )
    assert result.returncode == 0, result.stderr
    assert (host_output / "diagram.png").exists()
    assert (host_output / "diagram.png").stat().st_size > 0


def test_mcp_docker_workspace_relative_output(tmp_path: Path) -> None:
    cmd = compose_cmd()
    assert cmd is not None
    host_file = tmp_path / "docs" / "diagram.png"
    code = SAMPLE.read_text(encoding="utf-8")
    script = textwrap.dedent(
        f"""
        from pathlib import Path
        from mermaid_diagram.mcp_server import _resolve_output_path
        from mermaid_diagram.render import render_diagram_result

        code = {code!r}
        result = render_diagram_result(code, fmt="png")
        path = _resolve_output_path("docs/diagram.png")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(result)
        """
    ).strip()
    result = subprocess.run(
        [
            *cmd,
            "--profile",
            "mcp",
            "run",
            "--rm",
            "-T",
            "-v",
            f"{tmp_path}:/workspace",
            "-e",
            "MERMAID_WORKSPACE_ROOT=/workspace",
            "--entrypoint",
            "",
            "mcp",
            "uv",
            "run",
            "python",
            "-c",
            script,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert host_file.exists()
    assert host_file.stat().st_size > 0


@pytest.mark.parametrize("theme", ["default", "dark", "forest", "neutral"])
def test_mcp_docker_all_themes(theme: str) -> None:
    code = SAMPLE.read_text(encoding="utf-8")
    result = _run_render_in_container(code=code, fmt="png", theme=theme)
    assert result.returncode == 0, result.stderr
    png_data = base64.b64decode(result.stdout.strip())
    assert len(png_data) > 0


def test_mcp_docker_invalid_syntax() -> None:
    code = INVALID.read_text(encoding="utf-8")
    result = _run_render_in_container(code=code, fmt="png")
    assert result.returncode != 0
