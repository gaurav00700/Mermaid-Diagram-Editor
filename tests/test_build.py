"""Build smoke tests shared by all suites."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
