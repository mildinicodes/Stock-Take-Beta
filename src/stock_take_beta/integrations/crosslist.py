from __future__ import annotations

import json
import os
import re
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any, Callable

from playwright.sync_api import sync_playwright

DEBUG_PORT = 9223
GET_IMPORT_SHIMS_TOKEN = "/api/ProductImport/GetImportShims"
IMPORT_URLS = {
    "vinted": "https://app.crosslist.com/import/vinted",
    "ebay": "https://app.crosslist.com/import/ebay",
    "etsy": "https://app.crosslist.com/import/etsy",
}
ProgressCallback = Callable[[str], None]
_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", re.I)


class CrosslistConnectionError(RuntimeError):
    pass


def _find_chrome_executable() -> Path:
    for env_name in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        base = os.environ.get(env_name)
        if not base:
            continue
        path = Path(base) / "Google" / "Chrome" / "Application" / "chrome.exe"
        if path.exists():
            return path
    raise CrosslistConnectionError("Google Chrome could not be found on this PC.")


def _devtools_is_live(timeout: float = 1.0) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{DEBUG_PORT}/json/version", timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return bool(payload.get("webSocketDebuggerUrl"))
    except Exception:
        return False


def _launch_debug_chrome(profile_dir: Path, start_url: str) -> None:
    chrome = _find_chrome_executable()
    profile_dir.mkdir(parents=True, exist_ok=True)
    if _devtools_is_live():
        return
    subprocess.Popen([
        str(chrome),
        f"--remote-debugging-port={DEBUG_PORT}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--start-maximized",
        start_url,
    ])
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if _devtools_is_live():
            return
        time.sleep(0.5)
    raise CrosslistConnectionError("Chrome opened, but the Crosslist session could not be attached.")


class CrosslistBrowserClient:
    def __init__(self, profile_dir: Path, progress: ProgressCallback | None = None) -> None:
        self.profile_dir = Path(profile_dir)
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.progress = progress or (lambda _message: None)

    def _report(self, message: str) -> None:
        self.progress(message)

    @staticmethod
    def _listing_count(payload: dict[str, Any]) -> int:
        for key in ("items", "Items", "data", "Data", "results", "Results", "records", "Records"):
            value = payload.get(key)
            if isinstance(value, list):
                return len(value)
        return 0

    @staticmethod
    def _record_count(payload: dict[str, Any]) -> int:
        for key in ("records", "Records", "total", "Total", "count", "Count"):
            value = payload.get(key)
            if isinstance(value, int):
                return value
        return 0

    def fetch_marketplace(self, marketplace: str, timeout_seconds: int = 60) -> dict[str, Any]:
        marketplace = marketplace.lower()
        if marketplace not in IMPORT_URLS:
            raise ValueError(f"Unsupported marketplace: {marketplace}")

        url = IMPORT_URLS[marketplace]
        self._report(f"Opening Crosslist {marketplace.title()} Import...")
        if not _devtools_is_live():
            _launch_debug_chrome(self.profile_dir, url)

        captured: dict[str, Any] = {}
        request_template: dict[str, Any] = {}

        with sync_playwright() as playwright:
            browser = playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{DEBUG_PORT}", timeout=10_000)
            contexts = browser.contexts
            if not contexts:
                raise CrosslistConnectionError("Chrome opened but no browser context was available.")
            context = contexts[0]
            page = context.pages[0] if context.pages else context.new_page()

            def capture(response: Any) -> None:
                if GET_IMPORT_SHIMS_TOKEN not in response.url or response.request.method.upper() != "POST" or not response.ok:
                    return
                try:
                    payload = response.json()
                except Exception:
                    return
                if isinstance(payload, dict):
                    captured["payload"] = payload
                    request_template["url"] = response.url
                    request_template["body"] = response.request.post_data or ""
                    request_template["content_type"] = response.request.headers.get("content-type", "application/json")

            page.on("response", capture)
            page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            deadline = time.monotonic() + timeout_seconds
            while "payload" not in captured and time.monotonic() < deadline:
                page.wait_for_timeout(250)
            if "payload" not in captured:
                raise CrosslistConnectionError(f"No {marketplace.title()} inventory response was captured from Crosslist.")

            page_payload = captured["payload"]
            expected = self._record_count(page_payload)
            visible = self._listing_count(page_payload)
            if expected and visible >= expected:
                return page_payload

            request_url = request_template.get("url")
            if not request_url:
                return page_payload

            full_url = str(request_url).replace("fetchAll=false", "fetchAll=true")
            try:
                full_payload = page.evaluate(
                    """async ({url, body, contentType}) => {
                        const options = {method:'POST', credentials:'include', headers:{'Content-Type':contentType}};
                        if (body) options.body = body;
                        const response = await fetch(url, options);
                        if (!response.ok) throw new Error(`HTTP ${response.status}`);
                        return await response.json();
                    }""",
                    {
                        "url": full_url,
                        "body": request_template.get("body", ""),
                        "contentType": request_template.get("content_type", "application/json"),
                    },
                )
            except Exception:
                return page_payload
            return full_payload if isinstance(full_payload, dict) else page_payload


def valid_human_sku(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or _UUID_RE.fullmatch(text) or len(text) > 64:
        return None
    return text.upper()
