"""HTML content parser for Weixin articles."""

import re

from bs4 import BeautifulSoup


class WeixinParser:
    """Parse structured article data from a Weixin article page."""

    def parse(self, html: str, url: str) -> dict:
        """Parse article HTML into a structured response."""
        soup = BeautifulSoup(html, "html.parser")

        og_image = soup.find("meta", property="og:image")
        cover_url = og_image.get("content", "") if og_image else ""

        title_elem = soup.find("h1", {"id": "activity-name"})
        title = title_elem.get_text(strip=True) if title_elem else "未找到标题"

        author_elem = soup.find("span", {"id": "js_author_name"}) or soup.find(
            "a", {"id": "js_name"}
        )
        author = author_elem.get_text(strip=True) if author_elem else "未知作者"

        time_elem = soup.find("em", {"id": "publish_time"})
        publish_time = time_elem.get_text(strip=True) if time_elem else "未知时间"

        content_elem = soup.find("div", {"id": "js_content"})
        content = self._clean_content(content_elem) if content_elem else "未找到正文内容"

        return {
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "content": content,
            "cover_url": cover_url,
            "url": url,
        }

    def _clean_content(self, content_elem) -> str:
        """Convert the article body into readable plain text."""
        for tag in content_elem.find_all(["script", "style"]):
            tag.decompose()

        text = content_elem.get_text(separator="\n", strip=True)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        return text.strip()
