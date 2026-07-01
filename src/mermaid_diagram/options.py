import json
from pathlib import Path
from typing import Any

_CANDIDATE_PATHS = (
    Path(__file__).resolve().parents[2] / "export_options.json",
    Path.cwd() / "export_options.json",
)


def _options_path() -> Path:
    for candidate in _CANDIDATE_PATHS:
        if candidate.exists():
            return candidate
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
