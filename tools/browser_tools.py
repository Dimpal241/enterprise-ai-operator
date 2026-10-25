# tools/browser_tools.py
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from tools.base import BaseTool, ToolResult

EVIDENCE_DIR = Path("evidence/screenshots")


class BrowserSession:
    """Manages a persistent browser session across tool calls.

    Persistence is critical: the agent needs to stay logged in
    across multiple actions on the same portal.
    """

    _instance: Optional["BrowserSession"] = None

    def __init__(self):
        self._playwright = None
        self._browser = None
        self._page = None

    @classmethod
    def get_instance(cls) -> "BrowserSession":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def start(self, headless: bool = True):
        """Starts Playwright and launches Chromium."""
        if self._page and not self._page.is_closed():
            return self._page

        from playwright.sync_api import sync_playwright

        if self._playwright is None:
            self._playwright = sync_playwright().start()

        if self._browser is None:
            self._browser = self._playwright.chromium.launch(
                headless=headless,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )

        self._page = self._browser.new_page()
        return self._page

    def get_page(self, headless: bool = True):
        """Returns the active page, starting browser if not already running."""
        if self._page is None or self._page.is_closed():
            self.start(headless=headless)
        return self._page

    def stop(self):
        """Closes browser and stops Playwright."""
        if self._page and not self._page.is_closed():
            try:
                self._page.close()
            except Exception:
                pass
            self._page = None

        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None


class NavigateTool(BaseTool):
    name = "browser_navigate"
    description = "Navigate the browser to a URL. Use for opening web portals and pages."

    def __init__(self, session: Optional[BrowserSession] = None):
        self.session = session or BrowserSession.get_instance()

    def execute(self, url: str, **kwargs) -> ToolResult:
        try:
            page = self.session.get_page()
            response = page.goto(url, wait_until="load", timeout=30000)
            status_code = response.status if response else 200
            title = page.title()
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=f"Successfully navigated to {url} (status {status_code}). Page title: '{title}'",
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=f"Navigation failed for URL '{url}': {str(e)}",
            )

    def schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The destination URL to navigate to (e.g. http://localhost:8001/)",
                        }
                    },
                    "required": ["url"],
                },
            },
        }


class ClickTool(BaseTool):
    name = "browser_click"
    description = "Click an element on the current page. Specify by visible text, CSS selector, or ID (e.g. '#submit-btn')."

    def __init__(self, session: Optional[BrowserSession] = None):
        self.session = session or BrowserSession.get_instance()

    def execute(self, selector: str, **kwargs) -> ToolResult:
        try:
            page = self.session.get_page()
            page.wait_for_selector(selector, state="visible", timeout=10000)
            page.click(selector, timeout=10000)
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=f"Successfully clicked element matching '{selector}'",
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=f"Failed to click selector '{selector}': {str(e)}",
            )

    def schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector or element text to click (e.g. 'button[type=submit]', '#login-btn', 'text=Submit')",
                        }
                    },
                    "required": ["selector"],
                },
            },
        }


class TypeTool(BaseTool):
    name = "browser_type"
    description = "Type text into an input field on the current page."

    def __init__(self, session: Optional[BrowserSession] = None):
        self.session = session or BrowserSession.get_instance()

    def execute(self, selector: str, text: str, **kwargs) -> ToolResult:
        try:
            page = self.session.get_page()
            page.wait_for_selector(selector, state="visible", timeout=10000)
            page.fill(selector, text, timeout=10000)
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=f"Successfully filled input field '{selector}' with: '{text}'",
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=f"Failed to type into selector '{selector}': {str(e)}",
            )

    def schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector of the input field (e.g. '#username', 'input[name=vendor_name]')",
                        },
                        "text": {
                            "type": "string",
                            "description": "Text value to fill into the input field",
                        },
                    },
                    "required": ["selector", "text"],
                },
            },
        }


class ScreenshotTool(BaseTool):
    name = "browser_screenshot"
    description = "Take a screenshot of the current page state. Always call this after completing a major action to capture evidence."

    def __init__(self, session: Optional[BrowserSession] = None):
        self.session = session or BrowserSession.get_instance()

    def execute(self, label: str = "screenshot", **kwargs) -> ToolResult:
        try:
            EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_label = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in label)
            path = EVIDENCE_DIR / f"{timestamp}_{clean_label}.png"
            page = self.session.get_page()
            page.screenshot(path=str(path), full_page=True)
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=f"Screenshot saved: {path}",
                evidence=str(path),
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=f"Failed to take screenshot: {str(e)}",
            )

    def schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "label": {
                            "type": "string",
                            "description": "A short descriptive label for the screenshot (e.g. 'invoice_submitted', 'portal_login')",
                            "default": "screenshot",
                        }
                    },
                    "required": [],
                },
            },
        }


class ReadPageTextTool(BaseTool):
    name = "browser_read_page"
    description = "Extract all visible text from the current page. Use to read information displayed on screen."

    def __init__(self, session: Optional[BrowserSession] = None):
        self.session = session or BrowserSession.get_instance()

    def execute(self, **kwargs) -> ToolResult:
        try:
            page = self.session.get_page()
            text = page.inner_text("body", timeout=10000)
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=text.strip(),
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=f"Failed to read page text: {str(e)}",
            )

    def schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        }
