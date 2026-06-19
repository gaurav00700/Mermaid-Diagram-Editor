"""Integration tests for mermaid-diagram CLI and web build."""

from __future__ import annotations

import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
SAMPLE = EXAMPLES / "sample.mmd"
INVALID = EXAMPLES / "invalid.mmd"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "mermaid-diagram", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        handle.seek(16)
        width = int.from_bytes(handle.read(4), "big")
        height = int.from_bytes(handle.read(4), "big")
    return width, height


def test_export_options_loads() -> None:
    from mermaid_diagram.options import load_export_options

    options = load_export_options()
    assert options["defaultDpi"] == 96
    assert options["defaultPreviewBackground"] == "transparent"
    assert "dark" in options["themes"]


def test_cli_version() -> None:
    result = run_cli("version")
    assert result.returncode == 0
    assert "0.1.0" in result.stdout


def test_cli_render_svg(tmp_path: Path) -> None:
    output = tmp_path / "out.svg"
    result = run_cli("render", "-i", str(SAMPLE), "-o", str(output), "-f", "svg")
    assert result.returncode == 0, result.stderr
    content = output.read_text(encoding="utf-8")
    assert content.startswith("<svg")
    ET.fromstring(content)


def test_cli_render_png_dpi_scaling(tmp_path: Path) -> None:
    low = tmp_path / "low.png"
    high = tmp_path / "high.png"
    assert run_cli("render", "-i", str(SAMPLE), "-o", str(low), "--dpi", "96").returncode == 0
    assert run_cli("render", "-i", str(SAMPLE), "-o", str(high), "--dpi", "300").returncode == 0

    low_w, low_h = png_dimensions(low)
    high_w, high_h = png_dimensions(high)
    assert high_w > low_w
    assert high_h > low_h
    assert high_w / low_w == pytest.approx(300 / 96, rel=0.05)


def test_cli_missing_input_exits_nonzero() -> None:
    result = run_cli("render", "-i", "missing.mmd", "-o", "out.png")
    assert result.returncode != 0
    assert "does not exist" in result.stderr


def test_cli_invalid_syntax_exits_nonzero(tmp_path: Path) -> None:
    result = run_cli("render", "-i", str(INVALID), "-o", str(tmp_path / "bad.png"))
    assert result.returncode == 1
    assert "Render failed" in result.stderr


def test_web_build() -> None:
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=ROOT / "web",
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (ROOT / "web" / "dist" / "index.html").exists()
