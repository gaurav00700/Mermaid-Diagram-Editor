"""Browser E2E tests for the locally served web app."""

from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Page

from conftest import (
    assert_export_dialog_opens,
    assert_homepage_loads,
    assert_live_edit_updates_preview,
    assert_monaco_editor_loads,
    assert_preview_background_white,
    assert_preview_renders_sample_diagram,
    assert_reset_restores_sample_diagram,
    assert_reset_view_button,
    assert_upload_replaces_editor_content,
    assert_wheel_zoom_changes_scale,
    assert_zoom_controls_visible,
    assert_zoom_in_changes_label,
)

pytestmark = pytest.mark.web_local


def test_homepage_loads(page: Page, local_web_server: str) -> None:
    assert_homepage_loads(page, local_web_server)


def test_monaco_editor_loads(page: Page, local_web_server: str) -> None:
    assert_monaco_editor_loads(page, local_web_server)


def test_preview_renders_sample_diagram(page: Page, local_web_server: str) -> None:
    assert_preview_renders_sample_diagram(page, local_web_server)


def test_live_edit_updates_preview(page: Page, local_web_server: str) -> None:
    assert_live_edit_updates_preview(page, local_web_server)


def test_upload_replaces_editor_content(page: Page, local_web_server: str, tmp_path: Path) -> None:
    assert_upload_replaces_editor_content(page, local_web_server, tmp_path)


def test_reset_restores_sample_diagram(page: Page, local_web_server: str) -> None:
    assert_reset_restores_sample_diagram(page, local_web_server)


def test_zoom_controls_visible(page: Page, local_web_server: str) -> None:
    assert_zoom_controls_visible(page, local_web_server)


def test_zoom_in_changes_label(page: Page, local_web_server: str) -> None:
    assert_zoom_in_changes_label(page, local_web_server)


def test_wheel_zoom_changes_scale(page: Page, local_web_server: str) -> None:
    assert_wheel_zoom_changes_scale(page, local_web_server)


def test_reset_view_button(page: Page, local_web_server: str) -> None:
    assert_reset_view_button(page, local_web_server)


def test_preview_background_white(page: Page, local_web_server: str) -> None:
    assert_preview_background_white(page, local_web_server)


def test_export_dialog_opens(page: Page, local_web_server: str) -> None:
    assert_export_dialog_opens(page, local_web_server)
