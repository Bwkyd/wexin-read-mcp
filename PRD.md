# Weixin MCP 产品需求文档

## 1. 项目背景

### 1.1 项目概述
**项目名称**: Weixin MCP - 微信文章阅读器  
**项目类型**: Model Context Protocol (MCP) Server  
**目标**: 为大语言模型提供微信公众号文章内容获取能力

### 1.2 问题陈述
微信公众号文章存在以下技术限制：
- 内容需要浏览器环境渲染（动态加载）
- 存在反爬虫机制
- 大模型无法直接访问微信文章URL获取内容

### 1.3 解决方案
通过MCP协议实现一个服务端工具，使用Playwright浏览器自动化技术模拟真实浏览器访问，提取文章结构化内容，供大模型使用。

---

## 2. 典型用户用例

### 2.1 用例1：文章摘要生成
```
输入:
- URL: https://mp.weixin.qq.com/s/xxx
- 需求: "请总结这篇文章的主要观点"

处理流程:
1. AI调用 read_weixin_article 工具
2. MCP返回结构化数据:
   {
     "title": "文章标题",
     "author": "作者名",
     "publish_time": "2025-11-05",
     "content": "完整正文内容...",
     "success": true
   }
3. AI基于content字段生成摘要

预期输出:
"这篇文章主要讨论了..."
```

### 2.2 用例2：多篇文章对比分析
```
输入:
- URLs: [url1, url2, url3]
- 需求: "对比这三篇文章的观点差异"

处理流程:
1. AI顺序调用3次 read_weixin_article
2. 每次返回结构化数据
3. AI对比分析三篇文章的content

预期输出:
"第一篇文章认为...，第二篇文章强调...，第三篇文章则..."
```

### 2.3 用例3：内容验证与事实核查
```
输入:
- URL: https://mp.weixin.qq.com/s/xxx
- 需求: "验证文章中提到的数据是否准确"

处理流程:
1. AI调用工具获取文章内容
2. AI提取文章中的数据和引用
3. AI进行逻辑分析和已知知识对比

预期输出:
"文章提到的...数据与公开资料一致/存在差异"
```

### 2.4 测试用例设计视角
```python
# 测试数据结构
test_cases = [
    {
        "case_id": "TC001",
        "url": "https://mp.weixin.qq.com/s/valid_article_id",
        "expected_fields": ["title", "author", "publish_time", "content"],
        "expected_success": True,
        "description": "正常文章读取"
    },
    {
        "case_id": "TC002", 
        "url": "https://mp.weixin.qq.com/s/invalid_id",
        "expected_success": False,
        "expected_error": "Article not found",
        "description": "无效URL处理"
    },
    {
        "case_id": "TC003",
        "url": "https://mp.weixin.qq.com/s/deleted_article",
        "expected_success": False,
        "expected_error": "Article has been deleted",
        "description": "已删除文章处理"
    }
]
```

---

## 3. 技术选型与架构

### 3.1 核心技术栈
| 技术 | 版本 | 用途 | 选型理由 |
|------|------|------|----------|
| **Python** | 3.10+ | 开发语言 | fastmcp基于Python，生态成熟 |
| **fastmcp** | latest | MCP框架 | 简化MCP服务开发，提供装饰器模式 |
| **Playwright** | latest | 浏览器自动化 | 支持真实浏览器环境，绕过反爬虫 |
| **BeautifulSoup4** | 4.12+ | HTML解析 | 内容提取和清理 |

### 3.2 系统架构
```
┌─────────────┐         MCP Protocol        ┌──────────────────┐
│             │  <─────────────────────────> │                  │
│  AI Client  │         JSON-RPC            │   MCP Server     │
│  (Claude)   │                              │  (wx-mcp-server) │
│             │                              │                  │
└─────────────┘                              └────────┬─────────┘
                                                      │
                                                      │ Control
                                                      ▼
                                             ┌─────────────────┐
                                             │   Playwright    │
                                             │   Browser       │
                                             │   (Chromium)    │
                                             └────────┬────────┘
                                                      │
                                                      │ HTTP Request
                                                      ▼
                                             ┌─────────────────┐
                                             │  Weixin Server  │
                                             │  mp.weixin.qq.com│
                                             └─────────────────┘
```

### 3.3 项目结构
```
wx-mcp-server/
├── src/
│   ├── __init__.py
│   ├── server.py          # MCP服务主入口
│   ├── scraper.py         # Playwright爬虫逻辑
│   ├── parser.py          # 内容解析器
│   └── utils.py           # 工具函数
├── tests/
│   ├── test_scraper.py
│   └── test_parser.py
├── pyproject.toml         # 项目配置
├── requirements.txt       # 依赖管理
└── README.md
```

---

## 4. 核心流程

### 4.1 主流程图
```
[用户请求] → [AI识别URL] → [调用MCP工具]
                                    ↓
                            [启动Playwright浏览器]
                                    ↓
                            [访问微信文章URL]
                                    ↓
                            [等待页面完全加载]
                                    ↓
                            [提取DOM元素内容]
                                    ↓
                     ┌──────────────┴──────────────┐
                     ↓                             ↓
              [解析成功]                      [解析失败]
                     ↓                             ↓
            [结构化返回数据]                 [返回错误信息]
                     ↓                             ↓
                     └──────────────┬──────────────┘
                                    ↓
                            [关闭浏览器]
                                    ↓
                            [返回给AI处理]
```

### 4.2 数据流转
```
1. Input:  {"url": "https://mp.weixin.qq.com/s/xxx"}
2. Process: Browser → DOM → Parser → JSON
3. Output: {
     "title": string,
     "author": string,
     "publish_time": string,
     "content": string,
     "success": boolean,
     "error": string | null
   }
```

---

## 5. 关键技术实现

### 5.1 MCP服务器主入口 (`server.py`)
```python
from fastmcp import FastMCP
from scraper import WeixinScraper
import logging

# 初始化MCP服务
mcp = FastMCP("weixin-reader")

# 初始化爬虫
scraper = WeixinScraper()

@mcp.tool()
async def read_weixin_article(url: str) -> dict:
    """
    读取微信公众号文章内容
    
    Args:
        url: 微信文章URL，格式: https://mp.weixin.qq.com/s/xxx
        
    Returns:
        dict: {
            "success": bool,
            "title": str,
            "author": str,
            "publish_time": str,
            "content": str,
            "error": str | None
        }
    """
    try:
        # URL验证
        if not url.startswith("https://mp.weixin.qq.com/s/"):
            return {
                "success": False,
                "error": "Invalid URL format. Must be a Weixin article URL."
            }
        
        # 调用爬虫获取内容
        result = await scraper.fetch_article(url)
        return result
        
    except Exception as e:
        logging.error(f"Error fetching article: {e}")
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    # 启动MCP服务器
    mcp.run()
```

### 5.2 Playwright爬虫实现 (`scraper.py`)
```python
from playwright.async_api import async_playwright
from parser import WeixinParser
import asyncio

class WeixinScraper:
    def __init__(self):
        self.parser = WeixinParser()
        self.browser = None
        self.context = None
        
    async def initialize(self):
        """初始化浏览器"""
        if not self.browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                ]
            )
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
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
            
            # 访问URL，等待网络空闲
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # 等待关键元素加载
            await page.wait_for_selector('#js_content', timeout=10000)
            
            # 获取页面HTML
            html_content = await page.content()
            
            # 关闭页面
            await page.close()
            
            # 解析内容
            result = self.parser.parse(html_content, url)
            
            return {
                "success": True,
                **result,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fetch article: {str(e)}"
            }
    
    async def cleanup(self):
        """清理资源"""
        if self.browser:
            await self.browser.close()
```

### 5.3 内容解析器 (`parser.py`)
```python
from bs4 import BeautifulSoup
import re
from datetime import datetime

class WeixinParser:
    def parse(self, html: str, url: str) -> dict:
        """
        解析微信文章HTML
        
        Args:
            html: 页面HTML内容
            url: 文章URL
            
        Returns:
            dict: 解析后的结构化数据
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # 提取标题
        title_elem = soup.find('h1', {'id': 'activity-name'})
        title = title_elem.get_text(strip=True) if title_elem else "未找到标题"
        
        # 提取作者
        author_elem = soup.find('span', {'id': 'js_author_name'}) or \
                     soup.find('a', {'id': 'js_name'})
        author = author_elem.get_text(strip=True) if author_elem else "未知作者"
        
        # 提取发布时间
        time_elem = soup.find('em', {'id': 'publish_time'})
        publish_time = time_elem.get_text(strip=True) if time_elem else "未知时间"
        
        # 提取正文内容
        content_elem = soup.find('div', {'id': 'js_content'})
        if content_elem:
            # 清理内容
            content = self._clean_content(content_elem)
        else:
            content = "未找到正文内容"
        
        return {
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "content": content
        }
    
    def _clean_content(self, content_elem) -> str:
        """
        清理正文内容
        
        Args:
            content_elem: BeautifulSoup元素
            
        Returns:
            str: 清理后的纯文本内容
        """
        # 移除script和style标签
        for tag in content_elem.find_all(['script', 'style']):
            tag.decompose()
        
        # 获取文本内容
        text = content_elem.get_text(separator='\n', strip=True)
        
        # 清理多余空白
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        return text.strip()
```

### 5.4 项目配置 (`pyproject.toml`)
```toml
[project]
name = "wx-mcp-server"
version = "0.1.0"
description = "A MCP server for reading Weixin articles"
requires-python = ">=3.10"

dependencies = [
    "fastmcp>=0.1.0",
    "playwright>=1.40.0",
    "beautifulsoup4>=4.12.0",
    "lxml>=4.9.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### 5.5 安装与运行脚本
```bash
# 初始化项目
cd wx-mcp-server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -e .
playwright install chromium

# 运行服务
python src/server.py
```

---

## 6. 错误处理策略

### 6.1 错误类型与处理
| 错误类型 | 触发条件 | 处理方式 | 返回信息 |
|---------|---------|---------|---------|
| **URL格式错误** | URL不是微信文章链接 | 立即返回 | `"Invalid URL format"` |
| **网络超时** | 30秒内未加载完成 | 重试1次，失败返回 | `"Network timeout"` |
| **页面不存在** | 404或文章被删除 | 返回错误 | `"Article not found or deleted"` |
| **元素未找到** | 关键DOM元素缺失 | 返回部分数据 | 成功但字段为"未找到" |
| **浏览器崩溃** | Playwright异常 | 重启浏览器实例 | `"Browser error, please retry"` |

### 6.2 重试机制
```python
async def fetch_article_with_retry(self, url: str, max_retries: int = 2) -> dict:
    """带重试的文章获取"""
    for attempt in range(max_retries):
        try:
            result = await self.fetch_article(url)
            if result["success"]:
                return result
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # 指数退避
    
    return {"success": False, "error": "Max retries exceeded"}
```

---

## 7. 性能与优化

### 7.1 性能指标
- **响应时间**: < 10秒/文章
- **成功率**: > 95%
- **内存占用**: < 500MB

### 7.2 优化策略
1. **浏览器复用**: 保持浏览器实例，避免频繁启动
2. **并发控制**: 限制同时处理的请求数
3. **缓存机制**: 可选的文章内容缓存（避免重复请求）
4. **资源过滤**: 阻止图片/视频加载，只获取文本

```python
# 优化示例：阻止不必要的资源
await page.route("**/*.{png,jpg,jpeg,gif,svg,mp4}", lambda route: route.abort())
```

---

## 8. 安全与合规

### 8.1 使用限制
- 仅用于个人学习和研究
- 遵守微信公众平台服务协议
- 不进行高频爬取（建议间隔 > 2秒）
- 不用于商业用途

### 8.2 Rate Limiting
```python
from asyncio import Semaphore

class WeixinScraper:
    def __init__(self, max_concurrent=3):
        self.semaphore = Semaphore(max_concurrent)
    
    async def fetch_article(self, url: str):
        async with self.semaphore:
            # 限制并发数
            return await self._fetch_article_impl(url)
```

---

## 9. 测试要求

### 9.1 单元测试覆盖
- URL验证函数测试
- HTML解析函数测试
- 错误处理测试

### 9.2 集成测试
```python
# tests/test_integration.py
import pytest
from src.server import read_weixin_article

@pytest.mark.asyncio
async def test_read_valid_article():
    """测试读取有效文章"""
    url = "https://mp.weixin.qq.com/s/test_valid_article"
    result = await read_weixin_article(url)
    
    assert result["success"] is True
    assert "title" in result
    assert len(result["content"]) > 0

@pytest.mark.asyncio
async def test_read_invalid_url():
    """测试无效URL"""
    url = "https://invalid.com/article"
    result = await read_weixin_article(url)
    
    assert result["success"] is False
    assert "Invalid URL" in result["error"]
```

---

## 10. 部署与集成

### 10.1 MCP配置文件
在 Claude Desktop 配置中添加：
```json
{
  "mcpServers": {
    "weixin-reader": {
      "command": "python",
      "args": [
        "C:/Users/chenqimei/Desktop/wx-mcp/wx-mcp-server/src/server.py"
      ]
    }
  }
}
```

### 10.2 AI使用示例
```
用户: 请帮我总结这篇文章 https://mp.weixin.qq.com/s/xxx

AI内部流程:
1. 识别URL
2. 调用 read_weixin_article(url="https://mp.weixin.qq.com/s/xxx")
3. 接收返回数据
4. 基于content字段生成摘要

AI回复: 这篇《文章标题》由作者XXX发布于2025-11-05，主要讨论了...
```