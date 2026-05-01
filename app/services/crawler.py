"""Crawler service for network interception using Playwright."""

from dataclasses import dataclass, field
from playwright.async_api import Page, Request, Response
from app.core.browser_pool import browser_pool
from app.config import settings
import logging
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class InterceptedRequest:
    """Captured network request data."""

    url: str
    method: str
    resource_type: str
    headers: dict[str, str]


@dataclass
class Cookie:
    """Browser cookie data."""

    name: str
    value: str
    domain: str
    path: str
    secure: bool
    http_only: bool
    same_site: str | None


@dataclass
class CrawlerResult:
    """Complete data collected from crawling a domain."""

    domain: str
    requests: list[InterceptedRequest] = field(default_factory=list)
    js_files: list[str] = field(default_factory=list)
    cookies: list[Cookie] = field(default_factory=list)
    ads_txt_content: str | None = None
    page_title: str | None = None
    success: bool = False
    error: str | None = None


class CrawlerService:
    """Service for crawling publisher domains and intercepting network traffic."""

    async def scan_domain(self, domain: str) -> CrawlerResult:
        """
        Scan a domain and collect network requests, JS files, and cookies.

        Args:
            domain: Domain to scan (e.g., example.com)

        Returns:
            CrawlerResult with all collected data
        """
        result = CrawlerResult(domain=domain)

        context = None
        page = None

        try:
            # Create isolated browser context
            context = await browser_pool.create_context()

            # Set timeouts
            context.set_default_timeout(settings.page_load_timeout)
            context.set_default_navigation_timeout(settings.page_load_timeout)

            page = await context.new_page()

            # Data collection lists
            requests: list[InterceptedRequest] = []
            js_files: list[str] = []

            # Request handler
            async def handle_request(request: Request):
                try:
                    requests.append(
                        InterceptedRequest(
                            url=request.url,
                            method=request.method,
                            resource_type=request.resource_type,
                            headers=dict(request.headers),
                        )
                    )
                except Exception as e:
                    logger.debug(f"Error handling request: {e}")

            # Response handler (for capturing JS content)
            async def handle_response(response: Response):
                try:
                    if response.request.resource_type == "script":
                        # Only capture JS from successful responses
                        if response.status == 200:
                            try:
                                js_content = await response.text()
                                if js_content:
                                    js_files.append(js_content)
                            except Exception as e:
                                logger.debug(f"Could not read JS file: {e}")
                except Exception as e:
                    logger.debug(f"Error handling response: {e}")

            # Register handlers
            page.on("request", handle_request)
            page.on("response", handle_response)

            # Navigate to domain
            url = f"https://{domain}"
            logger.info(f"Navigating to {url}")

            try:
                await page.goto(url, wait_until="networkidle", timeout=settings.page_load_timeout)
            except Exception as nav_error:
                # Try HTTP if HTTPS fails
                logger.warning(f"HTTPS failed, trying HTTP: {nav_error}")
                url = f"http://{domain}"
                await page.goto(url, wait_until="networkidle", timeout=settings.page_load_timeout)

            # Wait a bit for any delayed scripts to load
            await asyncio.sleep(2)

            # Get page title
            try:
                result.page_title = await page.title()
            except Exception:
                pass

            # Get cookies
            cookies_raw = await context.cookies()
            result.cookies = [
                Cookie(
                    name=c.get("name", ""),
                    value=c.get("value", ""),
                    domain=c.get("domain", ""),
                    path=c.get("path", ""),
                    secure=c.get("secure", False),
                    http_only=c.get("httpOnly", False),
                    same_site=c.get("sameSite"),
                )
                for c in cookies_raw
            ]

            # Store collected data
            result.requests = requests
            result.js_files = js_files
            result.success = True

            logger.info(
                f"Scan complete: {len(requests)} requests, {len(js_files)} JS files, {len(result.cookies)} cookies"
            )

        except Exception as e:
            logger.error(f"Error scanning {domain}: {e}")
            result.error = str(e)
            result.success = False

        finally:
            # Cleanup
            if page:
                try:
                    await page.close()
                except Exception:
                    pass

            if context:
                try:
                    await context.close()
                except Exception:
                    pass

        return result

    async def fetch_ads_txt(self, domain: str) -> str | None:
        """
        Fetch ads.txt file from domain.

        Args:
            domain: Domain to fetch ads.txt from

        Returns:
            Content of ads.txt or None if not found
        """
        import httpx

        ads_txt_url = f"https://{domain}/ads.txt"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(ads_txt_url, follow_redirects=True)

                if response.status_code == 200:
                    return response.text

                # Try HTTP if HTTPS fails
                ads_txt_url = f"http://{domain}/ads.txt"
                response = await client.get(ads_txt_url, follow_redirects=True)

                if response.status_code == 200:
                    return response.text

        except Exception as e:
            logger.debug(f"Could not fetch ads.txt for {domain}: {e}")

        return None
