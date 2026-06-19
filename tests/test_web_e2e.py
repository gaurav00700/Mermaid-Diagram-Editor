"""Browser E2E tests for the built web app."""

from __future__ import annotations

import subprocess
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "web" / "dist"


class _Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST), **kwargs)


@pytest.fixture(scope="module")
def web_server() -> str:
    if not DIST.exists():
        subprocess.run(["npm", "run", "build"], cwd=ROOT / "web", check=True)

    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


def test_homepage_loads(page: Page, web_server: str) -> None:
    page.goto(web_server)
    page.get_by_role("heading", name="Mermaid Editor").wait_for()
    page.locator(".preview-header").get_by_text("Preview", exact=True).wait_for()


def test_preview_renders_sample_diagram(page: Page, web_server: str) -> None:
    page.goto(web_server)
    page.wait_for_selector(".preview-svg svg", timeout=5000)


def test_upload_replaces_editor_content(page: Page, web_server: str, tmp_path: Path) -> None:
    upload_file = tmp_path / "upload.mmd"
    upload_file.write_text("graph LR\n    X[Uploaded] --> Y[OK]\n", encoding="utf-8")

    page.goto(web_server)
    page.locator('input[type="file"]').set_input_files(str(upload_file))
    page.wait_for_selector(".preview-svg svg", timeout=5000)
    page.locator(".preview-svg").get_by_text("Uploaded", exact=True).wait_for()


def test_export_dialog_opens(page: Page, web_server: str) -> None:
    page.goto(web_server)
    page.get_by_role("button", name="Download").click()
    page.get_by_role("heading", name="Export Diagram").wait_for()
    page.get_by_role("button", name="Cancel").click()


def test_preview_background_changes_viewport(page: Page, web_server: str) -> None:
    page.goto(web_server)
    page.wait_for_selector(".preview-viewport", timeout=5000)
    page.locator(".preview-background-control select").select_option("white")

    background = page.locator(".preview-viewport").evaluate(
        "el => getComputedStyle(el).backgroundColor"
    )
    assert background in {"rgb(255, 255, 255)", "white"}


@pytest.fixture(scope="module")
def browser_context():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        yield context
        context.close()
        browser.close()


@pytest.fixture
def page(browser_context):
    page = browser_context.new_page()
    yield page
    page.close()
