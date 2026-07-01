from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer

from mermaid_diagram import history as history_store
from mermaid_diagram.options import get_default_source_filename, get_themes, load_export_options
from mermaid_diagram.render import preview_diagram, render_diagram

app = typer.Typer(
    name="mermaid-diagram",
    help="Render Mermaid diagrams to PNG or SVG from the command line.",
    no_args_is_help=True,
)

history_app = typer.Typer(help="Manage saved diagram sessions.")
source_app = typer.Typer(help="Export Mermaid source files.")

app.add_typer(history_app, name="history")
app.add_typer(source_app, name="source")


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


@source_app.command("export")
def source_export_command(
    input: Annotated[
        Path,
        typer.Option("--input", "-i", help="Input .mmd, .txt, or .md file", exists=True, readable=True),
    ],
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Output .mmd file path"),
    ] = None,
) -> None:
    """Write Mermaid source to a .mmd file."""
    resolved_output = output or Path(get_default_source_filename())
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    resolved_output.write_text(input.read_text(encoding="utf-8"), encoding="utf-8")
    typer.echo(f"Wrote {resolved_output}")


@history_app.command("list")
def history_list_command() -> None:
    """List saved diagram sessions."""
    entries = history_store.list_entries()
    if not entries:
        typer.echo("No saved sessions.")
        return
    for entry in entries:
        typer.echo(f"{entry['id']}  {entry['title']}  ({entry['updatedAt']})")


@history_app.command("save")
def history_save_command(
    input: Annotated[
        Path,
        typer.Option("--input", "-i", help="Input .mmd, .txt, or .md file", exists=True, readable=True),
    ],
    title: Annotated[
        Optional[str],
        typer.Option("--title", help="Session title"),
    ] = None,
) -> None:
    """Save a diagram file to history."""
    entry = history_store.save_from_file(input, title=title)
    typer.echo(f"Saved session {entry['id']} ({entry['title']})")


@history_app.command("new")
def history_new_command(
    title: Annotated[
        Optional[str],
        typer.Option("--title", help="Session title"),
    ] = None,
) -> None:
    """Create a new saved session from the default sample diagram."""
    entry = history_store.create_new_entry(title=title)
    typer.echo(f"Created session {entry['id']} ({entry['title']})")


@history_app.command("show")
def history_show_command(
    entry_id: Annotated[str, typer.Argument(help="History session id")],
) -> None:
    """Print Mermaid source for a saved session."""
    try:
        entry = history_store.get_entry(entry_id)
    except KeyError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(entry["code"], nl=False)


@history_app.command("export")
def history_export_command(
    entry_id: Annotated[str, typer.Argument(help="History session id")],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output .mmd file path"),
    ],
) -> None:
    """Export a saved session to a .mmd file."""
    try:
        history_store.export_entry(entry_id, output)
    except KeyError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Wrote {output}")


@history_app.command("delete")
def history_delete_command(
    entry_id: Annotated[str, typer.Argument(help="History session id")],
) -> None:
    """Delete a saved session."""
    try:
        history_store.delete_entry(entry_id)
    except KeyError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Deleted session {entry_id}")


def main() -> None:
    app()
