# Weixin Reader MCP

一个可安装、可分发的微信公众号文章阅读 MCP 服务。

## 特性

- 使用 Playwright 模拟真实浏览器访问微信文章
- 提取标题、作者、发布时间、封面图和正文内容
- 支持标准 Python 打包，可暴露 `weixin-reader` 命令

## 安装

### 本地开发

```bash
uv sync
uv run playwright install chromium
```

### 本地验证命令入口

在当前仓库目录下，可以直接这样运行：

```bash
uv run weixin-reader
```

也可以用 `uvx` 从本地项目启动：

```bash
uvx --from . weixin-reader
```

### 发布后全局使用

当这个项目发布到 PyPI，且包名为 `weixin-reader` 后，就可以直接：

```bash
uvx weixin-reader
```

## MCP 配置示例

### 方式 1：已发布到 PyPI

```json
{
  "mcpServers": {
    "weixin-reader": {
      "command": "uvx",
      "args": ["weixin-reader"]
    }
  }
}
```

### 方式 2：仓库本地开发态

```json
{
  "mcpServers": {
    "weixin-reader": {
      "command": "uvx",
      "args": ["--from", "/absolute/path/to/wexin-read-mcp", "weixin-reader"]
    }
  }
}
```

这样配置时，不再依赖 `python /某个绝对路径/src/server.py` 这种脚本路径。

## 使用示例

```
请帮我总结这篇文章：https://mp.weixin.qq.com/s/nEJhdxGea-KLZA_IGw9R5A
```

模型会调用 `read_weixin_article` 工具抓取并分析内容。

![示例截图](tu/0c7bbf3b419c36325c8e3e00fad207c6.png)

## 工具返回格式

### `read_weixin_article(url: str)`

参数：

- `url`: 微信文章 URL，例如 `https://mp.weixin.qq.com/s/xxx`

返回：

```json
{
  "success": true,
  "title": "文章标题",
  "author": "作者名",
  "publish_time": "2025-11-05",
  "content": "文章正文内容...",
  "cover_url": "https://...",
  "url": "https://mp.weixin.qq.com/s/xxx",
  "error": null
}
```

## 发布建议

如果你希望别人无需仓库路径、直接使用 `uvx weixin-reader`，还需要执行一次包发布：

```bash
uv build
uv publish
```

发布后，任意支持 MCP 的客户端都可以直接通过 `uvx weixin-reader` 启动它。

### GitHub Actions 自动发布

仓库现在已经包含两条工作流：

- `CI`：在 `push` / `pull_request` 时执行 `uv build`
- `Publish to PyPI`：在 GitHub Release 发布后自动上传到 PyPI

要让自动发布生效，你还需要在 PyPI 里为这个 GitHub 仓库配置 Trusted Publishing。配置完成后，发布流程通常是：

```bash
git tag v0.1.0
git push origin v0.1.0
```

然后在 GitHub 上创建对应的 Release，工作流就会自动把构建产物发布到 PyPI。

## 注意事项

- 仅用于个人学习和研究
- 请遵守微信公众平台服务协议
- 不建议高频抓取
- 首次运行前需要安装 Playwright Chromium 浏览器
