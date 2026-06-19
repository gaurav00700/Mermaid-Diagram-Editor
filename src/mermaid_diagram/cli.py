from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer

from mermaid_diagram.options import get_themes, load_export_options
from mermaid_diagram.render import preview_diagram, render_diagram

app = typer.Typer(
    name="mermaid-diagram",
    help="Render Mermaid diagrams to PNG or SVG from the command line.",
    no_args_is_help=True,
)


@app.command("version")
def version_command() -> None:
    """Show the installed package version."""
    typer.echo("mermaid-diagram 0.1.0")


@app.command("render")
def render_command(
    input: Annotated[
        Path,
        typer.Option("--input", "-i", help="Input .mmd, .txt, or .md file", exists=True, readable=True),
    ],
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Output file path"),
    ] = None,
    fmt: Annotated[
        Optional[str],
        typer.Option("--format", "-f", help="Output format: png or svg"),
    ] = None,
    dpi: Annotated[
        int,
        typer.Option("--dpi", help="PNG density base (scale = dpi / 96)"),
    ] = load_export_options()["defaultDpi"],
    background: Annotated[
        str,
        typer.Option("--background", "-b", help="Background: transparent, white, or #hex"),
    ] = load_export_options()["defaultBackground"],
    theme: Annotated[
        str,
        typer.Option("--theme", "-t", help="Mermaid theme"),
    ] = load_export_options()["defaultTheme"],
    scale: Annotated[
        float,
        typer.Option("--scale", "-s", help="Extra scale multiplier on top of DPI"),
    ] = 1.0,
) -> None:
    """Render a Mermaid source file to PNG or SVG."""
    if theme not in get_themes():
        typer.secho(
            f"Unknown theme '{theme}'. Choose from: {', '.join(get_themes())}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    resolved_output = output or input.with_suffix(f".{fmt or 'png'}")
    code = input.read_text(encoding="utf-8")

    try:
        render_diagram(
            code,
            resolved_output,
            fmt=fmt,
            dpi=dpi,
            background=background,
            theme=theme,
            scale=scale,
        )
    except Exception as exc:  # noqa: BLE001 - surface render failures to CLI user
        typer.secho(f"Render failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Wrote {resolved_output}")


@app.command("preview")
def preview_command(
    input: Annotated[
        Path,
        typer.Option("--input", "-i", help="Input .mmd, .txt, or .md file", exists=True, readable=True),
    ],
    background: Annotated[
        str,
        typer.Option("--background", "-b", help="Preview background: transparent, white, or #hex"),
    ] = load_export_options()["defaultPreviewBackground"],
    theme: Annotated[
        str,
        typer.Option("--theme", "-t", help="Mermaid theme"),
    ] = load_export_options()["defaultTheme"],
) -> None:
    """Open an interactive browser preview of a Mermaid diagram."""
    if theme not in get_themes():
        typer.secho(
            f"Unknown theme '{theme}'. Choose from: {', '.join(get_themes())}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    code = input.read_text(encoding="utf-8")

    try:
        typer.echo("Opening preview. Close the browser window to exit.")
        preview_diagram(code, background=background, theme=theme)
    except Exception as exc:  # noqa: BLE001 - surface preview failures to CLI user
        typer.secho(f"Preview failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc


def main() -> None:
    app()
