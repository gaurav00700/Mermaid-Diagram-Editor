"""Browser E2E tests for the Docker container web app."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from playwright.sync_api import Page

from conftest import (
    assert_export_dialog_opens,
    assert_homepage_loads,
    assert_live_edit_updates_preview,
    assert_preview_background_white,
    assert_preview_renders_sample_diagram,
    assert_upload_replaces_editor_content,
    assert_zoom_controls_visible,
    compose_cmd,
    ensure_web_build,
    first_asset_path,
)

pytestmark = pytest.mark.web_docker


def test_compose_health(docker_web_server: str) -> None:
    curl = subprocess.run(
        ["curl", "-sf", docker_web_server],
        text=True,
        capture_output=True,
        check=False,
    )
    assert curl.returncode == 0, curl.stderr
    assert "Mermaid Diagram Editor" in curl.stdout


def test_container_serves_html(page: Page, docker_web_server: str) -> None:
    page.goto(docker_web_server, wait_until="networkidle")
    assert "Mermaid Diagram Editor" in page.title()


def test_container_serves_static_assets(docker_web_server: str) -> None:
    ensure_web_build()
    asset_path = first_asset_path()
    curl = subprocess.run(
        ["curl", "-sf", "-o", "/dev/null", "-w", "%{http_code}", f"{docker_web_server}{asset_path}"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert curl.returncode == 0, curl.stderr
    assert curl.stdout.strip() == "200"


def test_homepage_loads(page: Page, docker_web_server: str) -> None:
    assert_homepage_loads(page, docker_web_server)


def test_preview_renders_sample_diagram(page: Page, docker_web_server: str) -> None:
    assert_preview_renders_sample_diagram(page, docker_web_server)


def test_live_edit_updates_preview(page: Page, docker_web_server: str) -> None:
    assert_live_edit_updates_preview(page, docker_web_server)


def test_upload_replaces_editor_content(page: Page, docker_web_server: str, tmp_path: Path) -> None:
    assert_upload_replaces_editor_content(page, docker_web_server, tmp_path)


def test_zoom_controls_visible(page: Page, docker_web_server: str) -> None:
    assert_zoom_controls_visible(page, docker_web_server)


def test_preview_background_white(page: Page, docker_web_server: str) -> None:
    assert_preview_background_white(page, docker_web_server)


def test_export_dialog_opens(page: Page, docker_web_server: str) -> None:
    assert_export_dialog_opens(page, docker_web_server)


def test_compose_cmd_available() -> None:
    assert compose_cmd() is not None
