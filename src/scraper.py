"""Playwright浏览器爬虫"""

from playwright.async_api import async_playwright, Browser, BrowserContext

# 支持相对导入和绝对导入
try:
    from .parser import WeixinParser
except ImportError:
    from parser import WeixinParser


class WeixinScraper:
    """微信文章爬虫"""
    
    def __init__(self):
        self.parser = WeixinParser()
        self.playwright = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
    
    async def initialize(self):
        """初始化浏览器"""
        if not self.browser:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                ]
            )
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
    
    async def fetch_article(self, url: str) -> dict:
        """
        获取微信文章内容
        
        Args:
            url: 文章URL
            
        Returns:
            dict: 包含文章数据的字典
        """
        try:
            await self.initialize()
            
            # 创建新页面
            page = await self.context.new_page()
            
            try:
                # 访问URL，等待网络空闲
                await page.goto(url, wait_until='networkidle', timeout=30000)
                
                # 等待关键元素加载
                await page.wait_for_selector('#js_content', timeout=10000)
                
                # 获取页面HTML
                html_content = await page.content()
                
                # 解析内容
                result = self.parser.parse(html_content, url)
                
                return {
                    "success": True,
                    **result,
                    "error": None
                }
            finally:
                # 确保页面关闭
                await page.close()
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fetch article: {str(e)}"
            }
    
    async def cleanup(self):
        """清理资源"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

