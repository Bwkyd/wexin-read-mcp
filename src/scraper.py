"""微信文章爬虫 - 委托 agent-browser (Rust + CDP + Chrome for Testing) 做反爬.

v0.2.0 起,原 Playwright 方案被微信加强反爬打穿(issue #3).
抓取层改为 subprocess 调用 agent-browser binary, 反爬内核由上游 Rust 项目维护.

前置要求: agent-browser 已装在 PATH 中
  brew install agent-browser
  # 或 npm install -g agent-browser
"""

import asyncio
import json
import shutil
import uuid

# 支持相对导入和绝对导入
try:
    from .parser import WeixinParser
except ImportError:
    from parser import WeixinParser


class AgentBrowserNotFound(RuntimeError):
    """agent-browser binary 未在 PATH 中."""


class WeixinScraper:
    """微信文章爬虫 - 通过 agent-browser binary 抓取."""

    def __init__(self):
        self.parser = WeixinParser()
        # 每个 WeixinScraper 实例独占一个 session 名
        self._session_name = f"weixin-mcp-{uuid.uuid4().hex[:8]}"
        self._session_active = False
        # MCP server 通常把 WeixinScraper 做全局单例,并发请求共享同一 session.
        # 同一 session 的两次 navigate 会冲突(后者把前者的 page 覆盖),故串行化.
        self._lock = asyncio.Lock()

    async def initialize(self):
        """验证 agent-browser 可用, 首次调用显式报错比抓取时报错更友好."""
        if not shutil.which("agent-browser"):
            raise AgentBrowserNotFound(
                "agent-browser binary not found in PATH.\n"
                "Install:\n"
                "  brew install agent-browser\n"
                "  # or: npm install -g agent-browser\n"
                "See: https://github.com/vercel-labs/agent-browser"
            )

    async def fetch_article(self, url: str) -> dict:
        """获取微信文章内容.

        Args:
            url: 文章URL

        Returns:
            dict: {success, title, author, publish_time, content, cover_url, error}
        """
        async with self._lock:
            try:
                await self.initialize()

                # 1. open URL (agent-browser 会自动启动/复用 session daemon)
                open_result = await self._run(
                    ["--session", self._session_name, "open", url, "--json"],
                    timeout=30,
                )
                if not open_result.get("success", False):
                    return {
                        "success": False,
                        "error": f"open failed: {open_result.get('error', 'unknown')}",
                    }
                self._session_active = True

                # 2. 等待微信正文容器渲染.等不到即反爬拦截页(无 #js_content),早停.
                wait_result = await self._run(
                    ["--session", self._session_name, "wait", "#js_content", "--json"],
                    timeout=15,
                )
                if not wait_result.get("success", False):
                    return {
                        "success": False,
                        "error": (
                            "wait for #js_content failed — likely anti-bot "
                            "interception page. detail: "
                            f"{wait_result.get('error', 'timeout')}"
                        ),
                    }

                # 3. 取整页 HTML (<html> 元素的 innerHTML)
                html_result = await self._run(
                    ["--session", self._session_name, "get", "html", "html", "--json"],
                    timeout=10,
                )
                if not html_result.get("success", False):
                    return {
                        "success": False,
                        "error": f"get html failed: {html_result.get('error')}",
                    }
                html = (
                    html_result.get("data", {}).get("html")
                    or html_result.get("html")
                    or ""
                )
                if not html:
                    return {"success": False, "error": "empty HTML response"}

                # 4. 解析 (复用原 parser.py, 保留 cover_url 等字段)
                parsed = self.parser.parse(html, url)
                return {"success": True, **parsed, "error": None}

            except AgentBrowserNotFound as e:
                return {"success": False, "error": str(e)}
            except asyncio.TimeoutError:
                return {"success": False, "error": "agent-browser subprocess timeout"}
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to fetch article: {type(e).__name__}: {e}",
                }

    async def cleanup(self):
        """关闭 session, 释放 agent-browser 对应的 daemon 进程."""
        if self._session_active:
            try:
                await self._run(
                    ["--session", self._session_name, "close"],
                    timeout=5,
                )
            except Exception:
                pass  # cleanup 失败不阻塞退出
            self._session_active = False

    async def _run(self, args: list, timeout: int) -> dict:
        """执行一次 agent-browser 子进程, 返回解析后的 JSON dict."""
        proc = await asyncio.create_subprocess_exec(
            "agent-browser",
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise

        if proc.returncode != 0:
            return {
                "success": False,
                "error": stderr.decode(errors="replace").strip()
                or f"exit code {proc.returncode}",
            }

        raw = stdout.decode(errors="replace").strip()
        if not raw:
            return {"success": True, "data": {}}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # 某些子命令可能返回纯文本, 封装成统一 shape
            return {"success": True, "data": {"raw": raw}}
