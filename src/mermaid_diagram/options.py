import json
from importlib import resources
from pathlib import Path
from typing import Any


def _options_path() -> Path:
    """Locate export_options.json for dev checkout, editable install, and uvx wheels."""
    candidates: list[Path] = []

    try:
        packaged = resources.files("mermaid_diagram").joinpath("export_options.json")
        with resources.as_file(packaged) as path:
            if path.is_file():
                candidates.append(path)
    except (FileNotFoundError, ModuleNotFoundError, TypeError):
        pass

    module_dir = Path(__file__).resolve().parent
    candidates.extend(
        (
            module_dir / "export_options.json",
            module_dir.parents[2] / "export_options.json",
            Path.cwd() / "export_options.json",
        )
    )

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file():
            return resolved

    raise FileNotFoundError("Could not locate export_options.json")


def load_export_options() -> dict[str, Any]:
    with _options_path().open(encoding="utf-8") as handle:
        return json.load(handle)


def get_themes() -> list[str]:
    return load_export_options()["themes"]


def get_max_history_entries() -> int:
    return int(load_export_options()["maxHistoryEntries"])


def get_default_source_filename() -> str:
    return str(load_export_options()["defaultSourceFilename"])
