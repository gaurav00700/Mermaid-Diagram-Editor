"""Docker smoke tests."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("docker-compose") is None, reason="docker-compose not installed")
def test_docker_compose_serves_app() -> None:
    compose = subprocess.run(
        ["docker-compose", "up", "-d"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert compose.returncode == 0, compose.stderr

    try:
        curl = subprocess.run(
            ["curl", "-sf", "http://localhost:8080/"],
            text=True,
            capture_output=True,
            check=False,
        )
        assert curl.returncode == 0, curl.stderr
        assert "Mermaid Diagram Editor" in curl.stdout
    finally:
        subprocess.run(["docker-compose", "down"], cwd=ROOT, check=False)
