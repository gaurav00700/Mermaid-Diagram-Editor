from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mermaid_diagram.options import get_max_history_entries

DEFAULT_SAMPLE = """flowchart TD
    A[Start] --> B{Is it working?}
    B -->|Yes| C[Great!]
    B -->|No| D[Debug]
    D --> B
"""


def _history_dir() -> Path:
    xdg = Path.home() / ".local" / "share" / "mermaid-diagram"
    xdg.mkdir(parents=True, exist_ok=True)
    return xdg


def store_path() -> Path:
    override = os.environ.get("MERMAID_DIAGRAM_HISTORY_FILE")
    if override:
        return Path(override)
    return _history_dir() / "history.json"


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def auto_title(code: str) -> str:
    for line in code.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped if len(stripped) <= 48 else f"{stripped[:45]}..."
    return "Untitled diagram"


def _trim_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    max_entries = get_max_history_entries()
    if len(entries) <= max_entries:
        return entries
    return sorted(entries, key=lambda item: item["updatedAt"], reverse=True)[:max_entries]


def load_store() -> dict[str, Any]:
    path = store_path()
    if not path.exists():
        return {"sessions": []}
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    sessions = data.get("sessions", [])
    if not isinstance(sessions, list):
        return {"sessions": []}
    return {"sessions": sessions}


def save_store(store: dict[str, Any]) -> None:
    sessions = store.get("sessions", [])
    if not isinstance(sessions, list):
        sessions = []
    trimmed = _trim_entries(sessions)
    path = store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump({"sessions": trimmed}, handle, indent=2)


def list_entries() -> list[dict[str, Any]]:
    store = load_store()
    sessions = store["sessions"]
    return sorted(sessions, key=lambda item: item.get("updatedAt", ""), reverse=True)


def get_entry(entry_id: str) -> dict[str, Any]:
    for entry in load_store()["sessions"]:
        if entry.get("id") == entry_id:
            return entry
    raise KeyError(f"History entry not found: {entry_id}")


def add_entry(code: str, title: str | None = None) -> dict[str, Any]:
    timestamp = _now_iso()
    entry = {
        "id": str(uuid.uuid4()),
        "title": title or auto_title(code),
        "code": code,
        "createdAt": timestamp,
        "updatedAt": timestamp,
    }
    store = load_store()
    store["sessions"].insert(0, entry)
    save_store(store)
    return entry


def delete_entry(entry_id: str) -> None:
    store = load_store()
    sessions = [entry for entry in store["sessions"] if entry.get("id") != entry_id]
    if len(sessions) == len(store["sessions"]):
        raise KeyError(f"History entry not found: {entry_id}")
    save_store({"sessions": sessions})


def save_from_file(path: Path, title: str | None = None) -> dict[str, Any]:
    code = path.read_text(encoding="utf-8")
    return add_entry(code, title=title or path.stem)


def export_entry(entry_id: str, output: Path) -> None:
    entry = get_entry(entry_id)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(entry["code"], encoding="utf-8")


def create_new_entry(title: str | None = None, code: str | None = None) -> dict[str, Any]:
    return add_entry(code or DEFAULT_SAMPLE, title=title)
