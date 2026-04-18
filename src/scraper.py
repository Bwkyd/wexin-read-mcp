"""微信文章爬虫 - 委托 url-md (Rust CLI,反爬 + Markdown 一步到位).

v0.3.0 起,抓取层从 agent-browser (4 subprocess 调用 + BeautifulSoup 解析)
简化为 url-md 单次调用。url-md 内部已处理:反爬 (reqwest 永久链 + CDP
回退 scaffold)、微信正文抽取、frontmatter 生成、Markdown 转换。

前置要求: url-md 已装在 PATH 中
  curl -fsSL https://raw.githubusercontent.com/Bwkyd/url-md/main/install.sh | bash

相比 v0.2.0 的改进:
- 4 subprocess → 1 subprocess
- 无需 session 锁(url-md 无状态)
- 无需 BeautifulSoup(url-md 已抽取)
- binary 7 MB vs agent-browser ~50 MB(含 Chrome-for-Testing)
"""

import asyncio
import shutil

import yaml


class UrlMdNotFound(RuntimeError):
    """url-md binary 未在 PATH 中."""


class WeixinScraper:
    """微信文章爬虫 - 通过 url-md CLI 抓取 Markdown,解析 frontmatter 返回结构化数据."""

    def __init__(self):
        # url-md 是无状态 CLI,每次 fetch 独立进程,无需 session / lock
        pass

    async def initialize(self):
        """验证 url-md 可用, 首次调用显式报错比抓取时报错更友好."""
        if not shutil.which("url-md"):
            raise UrlMdNotFound(
                "url-md binary not found in PATH.\n"
                "Install:\n"
                "  curl -fsSL https://raw.githubusercontent.com/Bwkyd/url-md/main/install.sh | bash\n"
                "See: https://github.com/Bwkyd/url-md"
            )

    async def fetch_article(self, url: str, timeout: int = 45) -> dict:
        """获取微信文章内容.

        Args:
            url: 文章URL
            timeout: url-md 子进程超时(秒)

        Returns:
            dict: {success, title, author, publish_time, content, cover_url, error}

            content 字段是 Markdown 格式(url-md 原生输出), 相比 v0.2.0 的纯文本
            保留了图片引用 / 代码块 / 列表结构 / 标题层级 等富文本信息.
        """
        try:
            await self.initialize()

            # 单次子进程调用 url-md: 抓取 + 反爬 + Markdown 转换一步到位
            # --quiet: 抑制 stderr 进度提示,stdout 只出 Markdown
            proc = await asyncio.create_subprocess_exec(
                "url-md",
                "md",
                url,
                "--quiet",
                "--timeout",
                str(timeout),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout + 5
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return {
                    "success": False,
                    "error": f"url-md subprocess timeout after {timeout}s",
                }

            if proc.returncode != 0:
                return {
                    "success": False,
                    "error": self._explain_exit_code(proc.returncode, stderr),
                }

            markdown = stdout.decode(errors="replace")
            return self._parse_markdown(markdown)

        except UrlMdNotFound as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fetch article: {type(e).__name__}: {e}",
            }

    async def cleanup(self):
        """url-md 无持久化 session, cleanup 是 no-op. 保留接口供 MCP server 调用."""
        return

    @staticmethod
    def _parse_markdown(md: str) -> dict:
        """从 url-md 输出解析 frontmatter + body.

        url-md 输出格式:
            ---
            title: ...
            author: ...
            publish_time: ...
            cover_url: ...
            ...
            ---

            <markdown body>
        """
        if not md.startswith("---\n"):
            # 无 frontmatter(不应发生),整段当 content
            return {
                "success": True,
                "title": "未找到标题",
                "author": "未知作者",
                "publish_time": "未知时间",
                "content": md.strip(),
                "cover_url": "",
                "error": None,
            }

        # 分离 frontmatter 与 body
        parts = md.split("---\n", 2)
        if len(parts) < 3:
            return {
                "success": False,
                "error": "malformed markdown: frontmatter delimiter missing",
            }

        try:
            fm = yaml.safe_load(parts[1]) or {}
        except yaml.YAMLError as e:
            return {
                "success": False,
                "error": f"frontmatter YAML parse failed: {e}",
            }

        body = parts[2].lstrip("\n")

        return {
            "success": True,
            "title": str(fm.get("title") or "未找到标题"),
            "author": str(fm.get("author") or "未知作者"),
            "publish_time": str(fm.get("publish_time") or "未知时间"),
            "content": body,
            "cover_url": str(fm.get("cover_url") or ""),
            "error": None,
        }

    @staticmethod
    def _explain_exit_code(code: int, stderr: bytes) -> str:
        """把 url-md 退出码翻译成人话."""
        stderr_text = stderr.decode(errors="replace").strip()
        meanings = {
            10: "network error",
            11: "blocked by anti-bot",
            12: "paywalled",
            13: "auth required",
            20: "parse/extract failed",
            30: "I/O error",
            99: "internal error",
        }
        hint = meanings.get(code, f"exit code {code}")
        return f"url-md failed ({hint}): {stderr_text}" if stderr_text else f"url-md failed ({hint})"
