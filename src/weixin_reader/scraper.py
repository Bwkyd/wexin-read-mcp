"""Playwright-based scraper for Weixin articles."""

from playwright.async_api import Browser, BrowserContext, async_playwright

from weixin_reader.parser import WeixinParser


class WeixinScraper:
    """Fetch and parse Weixin article pages."""

    def __init__(self):
        self.parser = WeixinParser()
        self.playwright = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None

    async def initialize(self):
        """Start Playwright and create a reusable browser context."""
        if self.browser:
            return

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

    async def fetch_article(self, url: str) -> dict:
        """Fetch a Weixin article and return structured content."""
        try:
            await self.initialize()
            page = await self.context.new_page()

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_selector("#js_content", timeout=10000)
                html_content = await page.content()
                result = self.parser.parse(html_content, url)

                return {
                    "success": True,
                    **result,
                    "error": None,
                }
            finally:
                await page.close()
        except Exception as exc:
            return {
                "success": False,
                "error": f"Failed to fetch article: {exc}",
            }

    async def cleanup(self):
        """Close browser resources cleanly."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
