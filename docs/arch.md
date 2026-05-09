# Life-assistant Architecture

> 基于 [nanobot](https://github.com/HKUDS/nanobot) · 个人开发 / 小团队定位 · Agent Loop + Skills · 受控工具调用 · 规则与模型混合

---

## 1. 整体定位

| 维度 | 说明 |
|------|------|
| **基座框架** | nanobot — 超轻量个人 AI Agent，提供 Agent Loop、Channel、Session、Memory、Tool 执行等基础设施 |
| **LLM 负责** | 理解用户意图、决定调用哪些工具、组织自然语言解释 |
| **传统代码负责** | 指标计算、回测引擎、条件筛选、数据校验、风控规则（以 nanobot Tool 形式注册） |
| **交互入口** | nanobot Gateway — 微信(weixin) / 企业微信(wecom) / Telegram / CLI / API 等多通道统一接入 |

### 1.1 为什么选择 nanobot

| 自研 | nanobot |
|------|---------|
| 需自建 Agent Loop、Channel 适配、Session 管理、Memory 层 | **全部开箱即用** |
| 需自写 微信接入 (WeChatFerry 等) | 内置 weixin channel，`nanobot channels login weixin` 扫码即用 |
| 需自建 工具注册 & schema 校验 | Agent Loop 原生支持 LLM function calling + tool execution |
| 需自建 上下文压缩 | 内置 Consolidator + Auto Compact |
| 需自建 长期记忆 | 内置 Dream（对话压缩 + 人格维护）+ **mem0**（语义长期记忆） |
| 需自建 多 LLM Provider 切换 | 内置 20+ Provider (OpenRouter / DeepSeek / Ollama / ...) |

---

## 2. 系统总览

```txt
用户
  │  微信 / 企业微信 / Telegram / CLI / API / WebSocket
  ▼
┌─────────────────────────────────────────────────────┐
│                  nanobot Gateway                    │
│   Channel Manager（allowFrom 鉴权 + 重试策略）        │
└────────────────────┬────────────────────────────────┘
                     │ 消息路由 → Session
                     ▼
┌─────────────────────────────────────────────────────┐
│                  Agent Loop                         │
│  1. 注入运行时上下文（时区、Skills 摘要、Memory）      │
│  2. 调用 LLM（function calling 模式）                │
│  3. 执行工具调用（内置工具 / MCP / 自定义 Skills）    │
│  4. 流式回复用户                                     │
└──────┬──────────────────────────┬───────────────────┘
       │                          │
       ▼                          ▼
┌─────────────┐          ┌─────────────────────┐
│  Tools 层   │          │    Memory 层              │
│  web_search │          │  mem0（语义长期记忆）       │
│  web_fetch  │          │  SOUL.md（人格）            │
│  shell exec │          │  history.jsonl             │
│  MCP Servers│          │  Consolidator→Dream        │
│  自定义 Tool │          └───────────────────────────┘
└──────┬──────┘
       │ (stdio)
       ▼
┌─────────────────┐
│ 本地 MCP Server │
│   (life-mcp)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   SQLite DB     │
│   life.db       │
└─────────────────┘
```

---

## 3. 渠道层（Channels）

| 渠道 | 接入方式 | 备注 |
|------|---------|------|
| 微信 (weixin) | `nanobot channels login weixin` 扫码 | 主要日常入口 |
| 企业微信 (wecom) | Bot ID + Bot Secret | 团队通知场景 |
| Telegram | Bot Token (@BotFather) | 备用入口，支持 inline buttons |
| CLI | `nanobot agent` | 本地调试 |
| API | OpenAI-compatible HTTP | 第三方集成 |
| WebSocket | `nanobot gateway` | WebUI / 自定义客户端 |

**鉴权**：每个渠道通过 `allowFrom` 白名单控制可访问的用户 ID；空列表默认拒绝所有请求。

**会话隔离**：默认每个 `channel × chat_id` 独立 Session；启用 `unifiedSession` 可跨渠道共享同一会话。

---

## 4. Agent Loop

```txt
收到消息
   │
   ├─ 注入上下文：运行时时间（timezone）、SOUL.md、USER.md、MEMORY.md、Skills 摘要
   │
   ├─ 调用 LLM（provider / model 可在 config 中切换）
   │      └─ LLM 返回 function_call → 执行工具 → 追加结果 → 再次调用 LLM
   │              （循环直到 LLM 不再发起 tool call）
   │
   ├─ 流式输出回复给用户（sendProgress = true）
   │
   └─ 触发 Consolidator（上下文超出阈值时压缩旧消息 → history.jsonl）
```

**上下文压缩策略**：

- **Token 驱动**（Consolidator）：对话超出上下文窗口时，将最旧安全片段摘要写入 `memory/history.jsonl`，不修改 session 文件，保留完整 tool call 轨迹。
- **空闲驱动**（Auto Compact）：用户空闲超过 `idleCompactAfterMinutes`（建议 15 分钟）后，自动压缩 session，降低下次请求的首 token 延迟。

---

## 5. Skills 系统

Skills 是本项目业务逻辑的主要载体，以目录形式存放于 `workspace/skills/`，由 Agent 按需调用。

```txt
workspace/
└── skills/
    ├── calendar/          # 日程管理：创建、查询、修改、提醒
    ├── todo/              # 待办事项（增删查改）
    └── reminder/          # 自然语言定时提醒（cron / at）
```

**运行机制**：

- Skill 目录中包含 `SKILL.md`（能力描述）+ 可选的可执行脚本/工具。
- Agent Loop 在提示词中注入 Skills 摘要；LLM 决定是否调用对应 Skill。
- 不需要的 Skill 可通过 `agents.defaults.disabledSkills` 禁用。

---

## 6. Memory 系统

本项目采用**双层记忆架构**，两层职责互不重叠：

| 层 | 技术 | 职责 | 持久化位置 |
|----|------|------|----------|
| 对话压缩层 | nanobot Dream | 压缩历史对话、维护 Agent 人格（SOUL.md） | `workspace/memory/` |
| 语义记忆层 | **mem0** | 跨会话长期事实记忆，支持自然语言语义检索 | mem0 本地向量存储 |

### 6.1 对话压缩层（nanobot Dream）

保留 nanobot 内置的 Consolidator + Dream 机制，负责：

- **上下文管理**：对话超出 token 窗口时，Consolidator 将旧消息摘要写入 `history.jsonl`
- **人格维护**：Dream 每 2 小时运行，维护 `SOUL.md`（Agent 沟通风格）
- **Auto Compact**：用户空闲超过 `idleCompactAfterMinutes` 后自动压缩 session

> `USER.md` / `MEMORY.md` 的用户画像职能移交给 mem0，不再依赖 Dream 更新。

**用户控制命令**：`/dream`（立即执行）、`/dream-log`（查看变更）、`/dream-restore`（回滚版本）。

### 6.2 语义记忆层（mem0）

mem0 负责跨会话的长期事实记忆，通过 `life-mcp` 暴露给 Agent Loop：

| 操作 | 触发时机 | 说明 |
|------|---------|------|
| `memory_add` | 对话中用户提及重要事实，或主动要求记录 | mem0 自动去重、合并冲突记忆 |
| `memory_search` | 每轮对话前，Agent 按当前话题召回相关记忆 | 语义向量相似度检索 |
| `memory_get_all` | 用户查询"你记得哪些关于我的事" | 返回全部记忆列表 |
| `memory_delete` | 用户要求遗忘某条记忆 | 按 ID 删除 |

**典型记忆内容**：用户偏好（"不喜欢早起"）、健康信息（"对花粉过敏"）、重要决策（"2026 年计划换工作"）、家庭信息（"父母在成都"）。

**本地部署**：mem0 使用本地向量后端（qdrant-local 或 chroma），无需云服务，数据不出本机。

---

## 7. Tools 层

### 7.1 内置工具

| 工具 | 说明 |
|------|------|
| `web_search` | 网页搜索，默认 DuckDuckGo，可切换 Brave / Tavily / Jina / Kagi |
| `web_fetch` | 抓取网页并转换为 Markdown（默认 Jina Reader，可本地降级） |
| `shell exec` | 执行 Shell 命令（可通过 bwrap 沙箱隔离，或完全禁用） |

### 7.2 MCP 工具

通过 `tools.mcpServers` 配置接入 MCP Server（兼容 Claude Desktop / Cursor 格式）：

- **Stdio**：本地进程（`npx` / `uvx` / `python`），**本项目自建 `life-mcp` 即采用此方式**
- **HTTP**：远程端点

### 7.3 本地 MCP Server 暴露的工具（life-mcp）

| 工具 | 操作 | 说明 |
|------|------|------|
| `task_create` | 创建 | 支持标题、描述、截止日（ISO 8601）、优先级、标签 |
| `task_list` | 查询 | 按状态 / 标签 / 关键词过滤 |
| `task_update` | 更新 | 修改任意字段（含状态流转） |
| `task_delete` | 删除 | 按 ID 删除 |
| `event_create` | 创建 | 支持开始/结束时间、地点、重复规则 |
| `event_list` | 查询 | 按时间范围过滤 |
| `event_update` | 更新 | — |
| `event_delete` | 删除 | — |
| `note_create` | 创建 | 支持标题、正文、标签 |
| `note_search` | 搜索 | SQLite FTS5 全文检索 |
| `note_update` | 更新 | — |
| `note_delete` | 删除 | — |
| `memory_add` | 写入 | 存储一条语义记忆，mem0 自动去重合并 |
| `memory_search` | 检索 | 按自然语言语义相似度召回相关记忆 |
| `memory_get_all` | 列举 | 获取全部已存储记忆 |
| `memory_delete` | 删除 | 按 ID 删除指定记忆 |

### 7.4 自定义 Skill Tool

在 Skills 目录中注册，以 nanobot Tool 形式向 Agent Loop 暴露，LLM 通过 function calling 调用。

---

## 8. 本地数据层

### 8.1 选型

| 维度 | 选择 | 理由 |
|------|------|------|
| 结构化存储 | Python stdlib `sqlite3`（WAL 模式） | 零额外依赖、单文件、支持 FTS5 全文检索、适合个人单写场景 |
| 语义记忆 | `mem0` | 专为 LLM Agent 设计；自动去重/合并冲突；支持本地向量后端，数据不出本机 |
| MCP Server 实现 | Python + `mcp[cli]` | 与 nanobot 同生态；stdio 传输无需开放端口 |
| 传输方式 | Stdio | 本地子进程，nanobot 直接 fork，无网络暴露 |

---

## 10. 部署方式

| 方式 | 适用场景 | 说明 |
|------|---------|------|
| 本地 CLI | 开发调试 | `nanobot agent` |
| macOS LaunchAgent | 个人长期运行 | plist 方式开机自启 |
| Docker | 服务器部署 | 官方镜像，非 root 运行，内置 bwrap |
| Linux systemd | VPS / 服务器 | `EnvironmentFile` 管理密钥 |

---

## 11. 安全设计

| 措施 | 配置项 | 说明 |
|------|--------|------|
| 渠道白名单 | `channels.*.allowFrom` | 空列表默认拒绝所有，须显式配置 |
| 工作区隔离 | `tools.restrictToWorkspace: true` | 文件操作限制在 workspace 目录内 |
| Shell 沙箱 | `tools.exec.sandbox: "bwrap"` | Linux 命名空间隔离，对外不可见 config 和密钥 |
| 禁用 Shell | `tools.exec.enable: false` | 完全移除 shell 工具 |
| 密钥外置 | `${ENV_VAR}` 引用 | 密钥不进入版本控制 |
| SSRF 防护 | 内置 SSRF 阻断 + `ssrfWhitelist` 白名单 | 防止 web_fetch 访问内网 |
