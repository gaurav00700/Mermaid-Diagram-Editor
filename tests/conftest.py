"""Shared pytest fixtures and helpers for CLI, local web, and Docker tests."""

from __future__ import annotations

import shutil
import subprocess
import threading
import time
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "web" / "dist"
EXAMPLES = ROOT / "examples"
SAMPLE = EXAMPLES / "sample.mmd"
INVALID = EXAMPLES / "invalid.mmd"


def compose_cmd() -> list[str] | None:
    if shutil.which("docker"):
        check = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if check.returncode == 0:
            return ["docker", "compose"]
    if shutil.which("docker-compose"):
        return ["docker-compose"]
    return None


def run_cli(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    return subprocess.run(
        ["uv", "run", "mermaid-diagram", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=full_env,
    )


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        handle.seek(16)
        width = int.from_bytes(handle.read(4), "big")
        height = int.from_bytes(handle.read(4), "big")
    return width, height


def ensure_web_build() -> None:
    if DIST.exists() and (DIST / "index.html").exists():
        return
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=ROOT / "web",
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stdout + result.stderr)


def first_asset_path() -> str:
    ensure_web_build()
    assets = list((DIST / "assets").glob("*.js"))
    if not assets:
        raise RuntimeError("No JS assets found in web/dist/assets")
    return f"/assets/{assets[0].name}"


class _StaticHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST), **kwargs)


@pytest.fixture(scope="module")
def local_web_server() -> str:
    ensure_web_build()
    server = ThreadingHTTPServer(("127.0.0.1", 0), _StaticHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


@pytest.fixture(scope="module")
def docker_web_server() -> str:
    cmd = compose_cmd()
    if cmd is None:
        pytest.skip("Docker Compose is not available")

    compose_up = subprocess.run(
        [*cmd, "up", "-d", "--build"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if compose_up.returncode != 0:
        pytest.skip(f"Docker compose up failed: {compose_up.stderr}")

    base_url = "http://localhost:8080"
    deadline = time.time() + 120
    ready = False
    while time.time() < deadline:
        curl = subprocess.run(
            ["curl", "-sf", base_url],
            text=True,
            capture_output=True,
            check=False,
        )
        if curl.returncode == 0 and "Mermaid Diagram Editor" in curl.stdout:
            ready = True
            break
        time.sleep(2)

    if not ready:
        subprocess.run([*cmd, "down"], cwd=ROOT, check=False)
        pytest.skip("Docker container did not become ready in time")

    yield base_url

    subprocess.run([*cmd, "down"], cwd=ROOT, check=False)


@pytest.fixture(scope="module")
def browser_context():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        yield context
        context.close()
        browser.close()


@pytest.fixture
def page(browser_context):
    test_page = browser_context.new_page()
    yield test_page
    test_page.close()


def assert_homepage_loads(page: Page, base_url: str) -> None:
    page.goto(base_url, wait_until="networkidle")
    page.get_by_role("heading", name="Mermaid Editor").wait_for()
    page.locator(".preview-header").get_by_text("Preview", exact=True).wait_for()


def assert_monaco_editor_loads(page: Page, base_url: str) -> None:
    page.goto(base_url, wait_until="networkidle")
    page.locator(".monaco-editor").wait_for(state="visible", timeout=10000)


def assert_preview_renders_sample_diagram(page: Page, base_url: str) -> None:
    page.goto(base_url, wait_until="networkidle")
    page.wait_for_selector(".preview-svg svg", timeout=15000)


def _set_monaco_content(page: Page, content: str) -> None:
    page.locator(".monaco-editor").click()
    page.keyboard.press("ControlOrMeta+A")
    page.keyboard.press("Backspace")
    page.keyboard.type(content)


def assert_live_edit_updates_preview(page: Page, base_url: str) -> None:
    page.goto(base_url, wait_until="networkidle")
    page.wait_for_selector(".preview-svg svg", timeout=15000)
    _set_monaco_content(page, "graph LR\n    Live[Works] --> OK[Docker]\n")
    page.locator(".preview-svg").get_by_text("Works", exact=True).wait_for(timeout=15000)


def assert_upload_replaces_editor_content(page: Page, base_url: str, tmp_path: Path) -> None:
    upload_file = tmp_path / "upload.mmd"
    upload_file.write_text("graph LR\n    X[Uploaded] --> Y[OK]\n", encoding="utf-8")

    page.goto(base_url, wait_until="networkidle")
    page.locator('input[type="file"]').set_input_files(str(upload_file))
    page.wait_for_selector(".preview-svg svg", timeout=15000)
    page.locator(".preview-svg").get_by_text("Uploaded", exact=True).wait_for()


def assert_reset_restores_sample_diagram(page: Page, base_url: str) -> None:
    page.goto(base_url, wait_until="networkidle")
    page.wait_for_selector(".preview-svg svg", timeout=15000)
    _set_monaco_content(page, "graph LR\n    Temp[Changed] --> End[Here]\n")
    page.locator(".preview-svg").get_by_text("Changed", exact=True).wait_for(timeout=15000)
    page.get_by_role("button", name="Reset", exact=True).click()
    page.locator(".preview-svg").get_by_text("Start", exact=True).wait_for(timeout=15000)


def assert_zoom_controls_visible(page: Page, base_url: str) -> None:
    page.goto(base_url, wait_until="networkidle")
    page.locator(".preview-zoom-controls").wait_for(state="visible")
    assert page.locator(".zoom-button").count() == 3


def assert_zoom_in_changes_label(page: Page, base_url: str) -> None:
    page.goto(base_url, wait_until="networkidle")
    page.wait_for_selector(".preview-svg svg", timeout=15000)
    before = page.locator(".preview-zoom-label").inner_text()
    page.get_by_role("button", name="Zoom in").click()
    after = page.locator(".preview-zoom-label").inner_text()
    assert before == "100%"
    assert after == "110%"


def assert_wheel_zoom_changes_scale(page: Page, base_url: str) -> None:
    page.goto(base_url, wait_until="networkidle")
    page.wait_for_selector(".preview-svg svg", timeout=15000)
    before = page.locator(".preview-zoom-label").inner_text()
    page.locator(".preview-viewport").hover()
    page.mouse.wheel(0, -120)
    page.wait_for_timeout(200)
    after = page.locator(".preview-zoom-label").inner_text()
    assert before == "100%"
    assert after == "110%"


def assert_reset_view_button(page: Page, base_url: str) -> None:
    page.goto(base_url, wait_until="networkidle")
    page.wait_for_selector(".preview-svg svg", timeout=15000)
    page.get_by_role("button", name="Zoom in").click()
    page.locator(".preview-viewport").hover()
    page.mouse.down()
    page.mouse.move(200, 200)
    page.mouse.up()
    page.get_by_role("button", name="Reset view").click()
    assert page.locator(".preview-zoom-label").inner_text() == "100%"


def assert_preview_background_white(page: Page, base_url: str) -> None:
    page.goto(base_url, wait_until="networkidle")
    page.wait_for_selector(".preview-viewport", timeout=15000)
    page.locator(".preview-background-control select").select_option("white")
    background = page.locator(".preview-viewport").evaluate(
        "el => getComputedStyle(el).backgroundColor"
    )
    assert background in {"rgb(255, 255, 255)", "white"}


def assert_export_dialog_opens(page: Page, base_url: str) -> None:
    page.goto(base_url, wait_until="networkidle")
    page.get_by_role("button", name="Export", exact=True).click()
    page.get_by_role("heading", name="Export Diagram").wait_for()
    page.get_by_role("button", name="Cancel").click()


def assert_history_panel_opens(page: Page, base_url: str) -> None:
    page.goto(base_url, wait_until="networkidle")
    page.get_by_role("button", name="History", exact=True).click()
    page.locator(".history-panel").wait_for(state="visible")
    page.locator(".history-session-list").wait_for(state="visible")


def assert_new_diagram_creates_session(page: Page, base_url: str) -> None:
    page.goto(base_url, wait_until="networkidle")
    page.get_by_role("button", name="History", exact=True).click()
    initial_count = page.locator(".history-session-item").count()
    page.get_by_role("button", name="New diagram").click()
    page.wait_for_timeout(300)
    assert page.locator(".history-session-item").count() == initial_count + 1


def assert_download_source_triggers_file(page: Page, base_url: str) -> None:
    page.goto(base_url, wait_until="networkidle")
    with page.expect_download() as download_info:
        page.get_by_role("button", name="Download", exact=True).click()
    download = download_info.value
    assert download.suggested_filename == "diagram.mmd"
    path = download.path()
    assert path is not None
    content = Path(path).read_text(encoding="utf-8")
    assert "flowchart" in content or "graph" in content


def assert_switch_session_updates_preview(page: Page, base_url: str) -> None:
    page.goto(base_url, wait_until="networkidle")
    page.wait_for_selector(".preview-svg svg", timeout=15000)
    page.get_by_role("button", name="History", exact=True).click()
    page.get_by_role("button", name="New diagram").click()
    _set_monaco_content(page, "graph LR\n    SessionB[Second] --> Done[OK]\n")
    page.locator(".preview-svg").get_by_text("Second", exact=True).wait_for(timeout=15000)
    sessions = page.locator(".history-session-item")
    assert sessions.count() >= 2
    sessions.nth(1).click()
    page.locator(".preview-svg").get_by_text("Start", exact=True).wait_for(timeout=15000)
