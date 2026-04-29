import asyncio
import base64
import json
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Error as PlaywrightError


# ---------------------------------------------------------------------------
# Persistent session support
#
# Set STORAGE_STATE_PATH to a writable JSON file path.  On startup (and after
# /session/load), the service reads that file into the browser context so
# cookies / localStorage are pre-populated.  After a successful human login you
# can call POST /session/save to persist the updated state back to the same
# file.
#
# Human one-time login procedure:
#   1. On the host machine run Playwright codegen / a headed script that logs
#      into cursor.com and calls `context.storage_state(path="state.json")`.
#   2. Copy state.json to the path referenced by STORAGE_STATE_PATH (e.g. a
#      Docker volume mount).
#   3. Restart (or call POST /session/load) so the service reloads the context.
#   4. Navigate to the protected page — the session is now authenticated.
# ---------------------------------------------------------------------------

STORAGE_STATE_PATH: str = os.environ.get(
    "STORAGE_STATE_PATH", "/data/session/storage_state.json"
)

browser: Browser | None = None
context: BrowserContext | None = None
page: Page | None = None
lock = asyncio.Lock()


async def get_browser() -> Browser:
    global browser
    if browser is None or not browser.is_connected():
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
    return browser


def _load_storage_state() -> dict | None:
    """Return storage state dict if the file exists, else None."""
    p = Path(STORAGE_STATE_PATH)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            return None
    return None


async def _make_context(br: Browser) -> BrowserContext:
    """Create a new browser context, optionally pre-loading stored auth state."""
    state = _load_storage_state()
    if state:
        ctx = await br.new_context(storage_state=state, viewport={"width": 1280, "height": 720})
    else:
        ctx = await br.new_context(viewport={"width": 1280, "height": 720})
    return ctx


async def get_page() -> Page:
    global browser, context, page
    br = await get_browser()
    if context is None:
        context = await _make_context(br)
    if page is None or page.is_closed():
        page = await context.new_page()
    return page


async def _reset_context() -> None:
    """Tear down existing context/page and rebuild from current storage state file."""
    global context, page
    if page and not page.is_closed():
        await page.close()
    if context:
        await context.close()
    page = None
    context = None
    # get_page() will recreate context + page on next call


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    global browser, context, page
    if page and not page.is_closed():
        await page.close()
    if context:
        await context.close()
    if browser:
        await browser.close()


app = FastAPI(title="BuyWhere Browser Automation Service", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Session management endpoints
# ---------------------------------------------------------------------------

class SessionLoadRequest(BaseModel):
    """Provide inline storage state JSON, or leave empty to reload from file."""
    storage_state: dict | None = None


@app.get("/session/status")
async def session_status():
    """Check whether a persisted auth state file exists."""
    p = Path(STORAGE_STATE_PATH)
    if p.exists():
        stat = p.stat()
        return {
            "status": "ok",
            "state_file": str(p),
            "exists": True,
            "size_bytes": stat.st_size,
            "modified_at": stat.st_mtime,
        }
    return {"status": "ok", "state_file": str(p), "exists": False}


@app.post("/session/save")
async def session_save():
    """
    Persist the current browser context's auth state (cookies, localStorage) to
    STORAGE_STATE_PATH.  Call this immediately after a successful login so the
    state survives restarts.
    """
    async with lock:
        if context is None:
            raise HTTPException(status_code=400, detail="No active browser context — navigate somewhere first.")
        try:
            state = await context.storage_state()
            dest = Path(STORAGE_STATE_PATH)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(state, indent=2))
            return {
                "status": "ok",
                "path": str(dest),
                "cookies": len(state.get("cookies", [])),
                "origins": len(state.get("origins", [])),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Save failed: {e}")


@app.post("/session/load")
async def session_load(req: SessionLoadRequest = SessionLoadRequest()):
    """
    Reload the browser context from a storage state.

    - If `storage_state` JSON is provided in the request body, write it to
      STORAGE_STATE_PATH first, then reload.
    - If omitted, reload from the existing STORAGE_STATE_PATH file.
    """
    async with lock:
        if req.storage_state is not None:
            dest = Path(STORAGE_STATE_PATH)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(req.storage_state, indent=2))
        if not Path(STORAGE_STATE_PATH).exists():
            raise HTTPException(status_code=400, detail="No storage state file found. Provide storage_state in the request body.")
        await _reset_context()
        # Rebuild immediately so next call to get_page() inherits the state.
        br = await get_browser()
        global context
        context = await _make_context(br)
        state = _load_storage_state()
        return {
            "status": "ok",
            "path": STORAGE_STATE_PATH,
            "cookies": len(state.get("cookies", [])) if state else 0,
            "origins": len(state.get("origins", [])) if state else 0,
        }


@app.delete("/session")
async def session_clear():
    """Delete the persisted auth state file and reset the browser context."""
    async with lock:
        await _reset_context()
        p = Path(STORAGE_STATE_PATH)
        if p.exists():
            p.unlink()
        return {"status": "ok", "cleared": True}


# ---------------------------------------------------------------------------
# Existing navigation / interaction endpoints (unchanged API surface)
# ---------------------------------------------------------------------------

class NavigateRequest(BaseModel):
    url: str
    timeout: int = 30000


class FillFormRequest(BaseModel):
    selector: str
    data: dict[str, str]


class ClickRequest(BaseModel):
    selector: str


class ScreenshotRequest(BaseModel):
    full_page: bool = False


class SubmitRequest(BaseModel):
    selector: str = "form"


class BrowserCommand(BaseModel):
    action: str
    params: dict[str, Any] = {}


@app.post("/navigate")
async def navigate(req: NavigateRequest):
    async with lock:
        p = await get_page()
        try:
            response = await p.goto(req.url, timeout=req.timeout, wait_until="networkidle")
            return {
                "status": "ok",
                "url": p.url,
                "title": await p.title(),
                "status_code": response.status if response else None
            }
        except PlaywrightError as e:
            raise HTTPException(status_code=500, detail=f"Navigation failed: {e}")


@app.post("/fill")
async def fill_form(req: FillFormRequest):
    async with lock:
        p = await get_page()
        try:
            for field, value in req.data.items():
                await p.fill(req.selector.replace("{field}", field), value)
            return {"status": "ok", "fields_filled": list(req.data.keys())}
        except PlaywrightError as e:
            raise HTTPException(status_code=500, detail=f"Fill failed: {e}")


@app.post("/click")
async def click(req: ClickRequest):
    async with lock:
        p = await get_page()
        try:
            await p.click(req.selector, timeout=10000)
            await p.wait_for_load_state("networkidle")
            return {"status": "ok", "selector": req.selector}
        except PlaywrightError as e:
            raise HTTPException(status_code=500, detail=f"Click failed: {e}")


@app.post("/screenshot")
async def screenshot(req: ScreenshotRequest):
    async with lock:
        p = await get_page()
        try:
            img = await p.screenshot(full_page=req.full_page)
            return {
                "status": "ok",
                "image": base64.b64encode(img).decode(),
                "format": "png"
            }
        except PlaywrightError as e:
            raise HTTPException(status_code=500, detail=f"Screenshot failed: {e}")


@app.post("/submit")
async def submit(req: SubmitRequest):
    async with lock:
        p = await get_page()
        try:
            await p.click(req.selector)
            await p.wait_for_load_state("networkidle")
            return {"status": "ok", "url": p.url}
        except PlaywrightError as e:
            raise HTTPException(status_code=500, detail=f"Submit failed: {e}")


@app.post("/execute")
async def execute(command: BrowserCommand):
    async with lock:
        p = await get_page()
        try:
            if command.action == "navigate":
                r = await p.goto(command.params["url"], timeout=command.params.get("timeout", 30000))
                return {"status": "ok", "url": p.url, "status": r.status if r else None}
            elif command.action == "fill":
                for selector, value in command.params.get("fields", {}).items():
                    await p.fill(selector, value)
                return {"status": "ok"}
            elif command.action == "click":
                await p.click(command.params["selector"])
                await p.wait_for_load_state("networkidle")
                return {"status": "ok"}
            elif command.action == "screenshot":
                img = await p.screenshot(full_page=command.params.get("full_page", False))
                return {"status": "ok", "image": base64.b64encode(img).decode()}
            elif command.action == "evaluate":
                result = await p.evaluate(command.params["script"])
                return {"status": "ok", "result": result}
            else:
                raise HTTPException(status_code=400, detail=f"Unknown action: {command.action}")
        except PlaywrightError as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    state_file_exists = Path(STORAGE_STATE_PATH).exists()
    return {
        "status": "ok",
        "service": "browser-automation",
        "session": {
            "state_file": STORAGE_STATE_PATH,
            "loaded": state_file_exists,
        }
    }


@app.get("/")
async def root():
    return {
        "service": "BuyWhere Browser Automation",
        "endpoints": [
            "/navigate", "/fill", "/click", "/screenshot", "/submit", "/execute",
            "/health",
            "/session/status", "/session/save", "/session/load", "/session (DELETE)",
        ]
    }
