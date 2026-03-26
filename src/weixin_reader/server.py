"""Main MCP server entrypoint."""

import asyncio
import logging

from fastmcp import FastMCP

from weixin_reader.scraper import WeixinScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("weixin-reader")
scraper = WeixinScraper()


@mcp.tool()
async def read_weixin_article(url: str) -> dict:
    """
    Read a Weixin public article.

    Args:
        url: Weixin article URL, like https://mp.weixin.qq.com/s/xxx

    Returns:
        dict: A structured article payload.
    """
    try:
        if not url.startswith("https://mp.weixin.qq.com/s/"):
            return {
                "success": False,
                "error": (
                    "Invalid URL format. Must be a Weixin article URL "
                    "(https://mp.weixin.qq.com/s/xxx)."
                ),
            }

        logger.info("Fetching article: %s", url)
        result = await scraper.fetch_article(url)

        if result.get("success"):
            logger.info("Successfully fetched: %s", result.get("title", "Unknown"))
        else:
            logger.error("Failed to fetch: %s", result.get("error"))

        return result
    except Exception as exc:
        logger.error("Error fetching article: %s", exc, exc_info=True)
        return {
            "success": False,
            "error": str(exc),
        }


async def cleanup():
    """Release browser resources before exit."""
    await scraper.cleanup()


def main():
    """Run the MCP server."""
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        asyncio.run(cleanup())


if __name__ == "__main__":
    main()
