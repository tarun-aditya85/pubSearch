"""Playwright browser pool manager for efficient resource usage."""

from playwright.async_api import async_playwright, Browser, Playwright
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class BrowserPool:
    """
    Singleton browser pool manager.
    Maintains a single browser instance with multiple contexts per scan.
    """

    def __init__(self):
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    async def initialize(self):
        """Start Playwright and launch browser."""
        if self._browser is not None:
            logger.info("Browser already initialized")
            return

        logger.info("Initializing Playwright browser...")
        self._playwright = await async_playwright().start()

        self._browser = await self._playwright.chromium.launch(
            headless=settings.headless,
            args=settings.browser_args,
        )

        logger.info("Browser initialized successfully")

    async def cleanup(self):
        """Close browser and stop Playwright."""
        if self._browser:
            await self._browser.close()
            self._browser = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

        logger.info("Browser pool cleaned up")

    async def get_browser(self) -> Browser:
        """Get the shared browser instance."""
        if self._browser is None:
            await self.initialize()

        if self._browser is None:
            raise RuntimeError("Failed to initialize browser")

        return self._browser

    async def create_context(self):
        """Create a new browser context for isolated scanning."""
        browser = await self.get_browser()

        context = await browser.new_context(
            viewport={"width": settings.viewport_width, "height": settings.viewport_height},
            user_agent=settings.user_agent,
            ignore_https_errors=True,  # Don't fail on SSL errors
        )

        return context


# Global singleton instance
browser_pool = BrowserPool()
