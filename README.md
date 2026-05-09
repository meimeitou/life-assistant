# life-assistant

基于 [nanobot](https://github.com/HKUDS/nanobot) 的个人生活助理，通过 MCP 工具服务提供待办、日历、笔记、账本和提醒功能。

## 依赖

- [nanobot](https://github.com/HKUDS/nanobot) >= 0.1.5
- [uv](https://docs.astral.sh/uv/)

## 快速开始

**1. 安装 Python 依赖**

```sh
uv sync
```

**2. 配置环境变量**

```sh
cp .env.example .env
# 编辑 .env，填入 API Key 和模型名称
```

**3. 启动**

需要先安装 nanobot:

```bash
# install
pip install nanobot-ai
# or
uv tool install nanobot-ai

# upgrade
uv tool upgrade nanobot-ai
# or
pip install -U nanobot-ai
```

然后运行：

```sh
./start.sh
```

`start.sh` 会自动：从 `.env` 加载变量 → 渲染 `config.json` → 初始化数据库 → 启动 nanobot。

**渠道配置**（可选）：编辑生成的 `config.json`，启用 telegram / websocket 等渠道后重新运行 `./start.sh`。

## 项目结构

```
mcp-server/    # MCP 工具服务（任务/日历/笔记/账本/记忆）
workspace/     # nanobot workspace（SOUL.md + skills/）
docs/          # 架构与功能设计文档
```
