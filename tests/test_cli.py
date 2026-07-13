"""CLI tests for mermaid-diagram render and preview commands."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from conftest import INVALID, SAMPLE, png_dimensions, run_cli

pytestmark = pytest.mark.cli


def test_export_options_loads() -> None:
    from mermaid_diagram.options import _options_path, load_export_options

    options = load_export_options()
    assert options["defaultDpi"] == 96
    assert options["defaultPreviewBackground"] == "transparent"
    assert options["maxHistoryEntries"] == 50
    assert "dark" in options["themes"]
    assert _options_path().name == "export_options.json"
    assert "mermaid_diagram" in _options_path().as_posix()


def test_wheel_includes_export_options() -> None:
    import subprocess
    import zipfile

    from conftest import ROOT

    build = subprocess.run(
        ["uv", "build"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert build.returncode == 0, build.stderr
    wheel = next((ROOT / "dist").glob("*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
    assert "mermaid_diagram/export_options.json" in names


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


def test_cli_render_png_default(tmp_path: Path) -> None:
    output = tmp_path / "out.png"
    result = run_cli("render", "-i", str(SAMPLE), "-o", str(output))
    assert result.returncode == 0, result.stderr
    assert output.exists()
    assert output.stat().st_size > 0


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


def test_cli_render_svg_with_background_white(tmp_path: Path) -> None:
    output = tmp_path / "out.svg"
    result = run_cli(
        "render",
        "-i",
        str(SAMPLE),
        "-o",
        str(output),
        "-f",
        "svg",
        "--background",
        "white",
    )
    assert result.returncode == 0, result.stderr
    content = output.read_text(encoding="utf-8")
    assert 'fill="#ffffff"' in content or "fill='#ffffff'" in content


def test_cli_render_png_with_background_white(tmp_path: Path) -> None:
    transparent = tmp_path / "transparent.png"
    white = tmp_path / "white.png"
    assert (
        run_cli("render", "-i", str(SAMPLE), "-o", str(transparent), "--background", "transparent").returncode
        == 0
    )
    assert run_cli("render", "-i", str(SAMPLE), "-o", str(white), "--background", "white").returncode == 0
    assert white.stat().st_size > 0


@pytest.mark.parametrize("theme", ["default", "dark", "forest", "neutral"])
def test_cli_render_with_theme(tmp_path: Path, theme: str) -> None:
    output = tmp_path / f"{theme}.png"
    result = run_cli("render", "-i", str(SAMPLE), "-o", str(output), "--theme", theme)
    assert result.returncode == 0, result.stderr
    assert output.exists()


def test_cli_render_with_scale(tmp_path: Path) -> None:
    base = tmp_path / "base.png"
    scaled = tmp_path / "scaled.png"
    assert run_cli("render", "-i", str(SAMPLE), "-o", str(base), "--dpi", "96", "--scale", "1").returncode == 0
    assert run_cli("render", "-i", str(SAMPLE), "-o", str(scaled), "--dpi", "96", "--scale", "2").returncode == 0

    base_w, _ = png_dimensions(base)
    scaled_w, _ = png_dimensions(scaled)
    assert scaled_w > base_w
    assert scaled_w / base_w == pytest.approx(2.0, rel=0.05)


def test_cli_render_default_output_path(tmp_path: Path) -> None:
    input_copy = tmp_path / "sample.mmd"
    input_copy.write_text(SAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    result = run_cli("render", "-i", str(input_copy))
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "sample.png").exists()


def test_cli_missing_input_exits_nonzero() -> None:
    result = run_cli("render", "-i", "missing.mmd", "-o", "out.png")
    assert result.returncode != 0
    assert "does not exist" in result.stderr


def test_cli_invalid_syntax_exits_nonzero(tmp_path: Path) -> None:
    result = run_cli("render", "-i", str(INVALID), "-o", str(tmp_path / "bad.png"))
    assert result.returncode == 1
    assert "Render failed" in result.stderr


def test_cli_invalid_theme_exits_nonzero(tmp_path: Path) -> None:
    result = run_cli("render", "-i", str(SAMPLE), "-o", str(tmp_path / "bad.png"), "--theme", "unknown")
    assert result.returncode == 1
    assert "Unknown theme" in result.stderr


def test_cli_preview_invalid_theme_exits_nonzero() -> None:
    result = run_cli("preview", "-i", str(SAMPLE), "--theme", "unknown")
    assert result.returncode == 1
    assert "Unknown theme" in result.stderr


def test_cli_preview_missing_input_exits_nonzero() -> None:
    result = run_cli("preview", "-i", "missing.mmd")
    assert result.returncode != 0
    assert "does not exist" in result.stderr


def test_cli_source_export(tmp_path: Path) -> None:
    output = tmp_path / "copy.mmd"
    result = run_cli("source", "export", "-i", str(SAMPLE), "-o", str(output))
    assert result.returncode == 0, result.stderr
    assert output.read_text(encoding="utf-8") == SAMPLE.read_text(encoding="utf-8")


def test_cli_history_save_list_export_delete(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store_file = tmp_path / "history.json"
    monkeypatch.setenv("MERMAID_DIAGRAM_HISTORY_FILE", str(store_file))

    save = run_cli("history", "save", "-i", str(SAMPLE), "--title", "Sample session")
    assert save.returncode == 0, save.stderr
    session_id = save.stdout.strip().split()[2]

    listed = run_cli("history", "list")
    assert listed.returncode == 0, listed.stderr
    assert "Sample session" in listed.stdout

    exported = tmp_path / "restored.mmd"
    export_result = run_cli("history", "export", session_id, "-o", str(exported))
    assert export_result.returncode == 0, export_result.stderr
    assert exported.read_text(encoding="utf-8") == SAMPLE.read_text(encoding="utf-8")

    delete_result = run_cli("history", "delete", session_id)
    assert delete_result.returncode == 0, delete_result.stderr
    empty = run_cli("history", "list")
    assert "No saved sessions." in empty.stdout


def test_cli_history_new(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store_file = tmp_path / "history.json"
    monkeypatch.setenv("MERMAID_DIAGRAM_HISTORY_FILE", str(store_file))

    result = run_cli("history", "new", "--title", "Fresh")
    assert result.returncode == 0, result.stderr
    assert "Fresh" in result.stdout

    listed = run_cli("history", "list")
    assert "Fresh" in listed.stdout

