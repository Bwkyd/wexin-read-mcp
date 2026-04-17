# Weixin MCP - 微信文章阅读器

一个极简的MCP，让大模型能够阅读微信公众号文章。

## 核心功能

- 🎭 **浏览器模拟**：使用 Playwright 完整模拟浏览器环境
- 📝 **内容提取**：自动提取标题、作者、发布时间、正文内容
- ⚡ **简洁实现**：最少的代码实现核心功能

## 工作流程

1. 用户发送URL和需求给大模型
2. 大模型调用MCP工具
3. MCP获取文章内容发送给大模型
4. 大模型根据文章内容输出自然语言

## 技术栈

- **Python 3.10+**
- **fastmcp** - MCP框架
- **agent-browser** (Rust + Chrome for Testing + 裸 CDP) - 反爬抓取内核,外部二进制依赖
- **BeautifulSoup4** - HTML解析

> **v0.2.0 升级说明**: 原 Playwright 方案被微信加强反爬打穿 ([issue #3](https://github.com/Bwkyd/wexin-read-mcp/issues/3))。抓取层改为委托给 [agent-browser](https://github.com/vercel-labs/agent-browser)(Apache-2.0 开源 Rust 项目),反爬内核由上游维护升级。MCP 协议/接口零变化,现有 Claude/Cursor 配置不需要调整。

## 快速开始

### 1. 安装 agent-browser (反爬内核,v0.2.0 起必需)

```bash
# 推荐: Homebrew (macOS)
brew install agent-browser

# 或: npm 全局安装
npm install -g agent-browser

# 验证
agent-browser --version

# 首次运行会自动下载 Chrome for Testing (~150 MB),按提示确认即可
agent-browser install
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3. 配置

```json
{
  "mcpServers": {
    "weixin-reader": {
      "command": "python",
      "args": [
        "C:/Users/你的用户名/Desktop/wx-mcp/wx-mcp-server/src/server.py"
      ]
    }
  }
}
```

**注意**: 请将路径替换为你的实际项目路径。


## 使用示例

在Claude中直接使用：

```
请帮我总结这篇文章：https://mp.weixin.qq.com/s/nEJhdxGea-KLZA_IGw9R5A
```

Claude会自动调用`read_weixin_article`工具获取文章内容并进行分析。
![alt text](tu/0c7bbf3b419c36325c8e3e00fad207c6.png)


## 功能说明

### `read_weixin_article(url: str)`

读取微信公众号文章内容。

**参数**:
- `url`: 微信文章URL，格式: `https://mp.weixin.qq.com/s/xxx`

**返回**:
```json
{
  "success": true,
  "title": "文章标题",
  "author": "作者名",
  "publish_time": "2025-11-05",
  "content": "文章正文内容...",
  "error": null
}
```

## 注意事项

- ⚠️ 仅用于个人学习和研究
- ⚠️ 遵守微信公众平台服务协议
- ⚠️ 不建议高频爬取（建议间隔 > 2秒）
- ⚠️ 不用于商业用途
