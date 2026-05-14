# MomentYY - 全能 AI 工作助手

基于 LangGraph + FastAPI + Vue3 的 AI Agent 全栈应用，支持 Web 对话界面和钉钉机器人接入。

## 功能特性

- 🧠 **智能对话**：基于 LangGraph 的 ReAct 范式，自动判断是否需要调用工具
- 🔧 **工具系统**：内置天气查询、活动推荐，可扩展更多工具
- 💾 **对话记忆**：按用户/会话隔离，支持跨请求上下文保持
- 🌐 **Web 界面**：Vue3 + element-ai-vue 组件库，支持日夜模式切换
- 🤖 **钉钉机器人**：Stream 模式接入，无需公网地址，群聊 @机器人 即可使用
- 🔌 **可扩展架构**：加新工具只需 3 步（写函数 → 注册 → 加描述）

## 项目结构

```
LangGraph-Agent/
├── server/                          # 后端（Python + FastAPI + LangGraph）
│   ├── app/
│   │   ├── main.py                  # FastAPI 入口
│   │   ├── config.py                # 配置管理
│   │   ├── dingtalk_bot.py          # 钉钉机器人（Stream 模式）
│   │   ├── api/
│   │   │   └── chat.py              # POST /api/chat
│   │   ├── agent/
│   │   │   ├── graph.py             # LangGraph 图定义
│   │   │   ├── state.py             # AgentState
│   │   │   ├── llm.py              # MiMo LLM 适配层
│   │   │   ├── nodes/
│   │   │   │   ├── router.py       # 路由节点（决定调不调工具）
│   │   │   │   └── tool_executor.py # 工具执行节点
│   │   │   └── tools/
│   │   │       ├── weather.py       # 天气查询
│   │   │       └── recommend.py     # 活动推荐
│   │   └── memory/
│   │       └── conversation.py      # 对话历史持久化
│   ├── data/
│   │   └── memory/                  # 对话记录存储（按用户隔离）
│   ├── .env.example                 # 环境变量模板
│   └── requirements.txt
│
├── web/                             # 前端（Vue3 + TS + Vite + element-ai-vue）
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue                  # 布局编排
│   │   ├── api/
│   │   │   └── chat.ts             # API 请求
│   │   └── components/
│   │       ├── Sidebar.vue          # 侧边栏（会话列表 + 日夜切换）
│   │       ├── EmptyState.vue       # 空状态（居中输入框）
│   │       ├── MessageList.vue      # 消息气泡列表
│   │       └── ChatInput.vue        # 输入框
│   ├── vite.config.ts
│   └── package.json
│
├── .gitignore
└── README.md
```

## 快速开始

### 1. 配置环境变量

```bash
cd server
cp .env.example .env
# 编辑 .env，填入你的 LLM API Key
```

### 2. 启动后端

```bash
cd server
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/uvicorn app.main:app --port 8000
```

### 3. 启动前端

```bash
cd web
npm install
npm run dev
```

访问 http://localhost:3000

### 4. 启动钉钉机器人（可选）

```bash
cd server
./venv/bin/python -m app.dingtalk_bot
```

需要在 `.env` 中配置 `DINGTALK_CLIENT_ID` 和 `DINGTALK_CLIENT_SECRET`。

## API 接口

| 方法 | 路径 | 功能 |
|---|---|---|
| POST | `/api/chat` | 核心对话接口 |
| GET | `/api/memory/{session_id}` | 查看对话历史 |
| DELETE | `/api/memory/{session_id}` | 清除对话历史 |
| GET | `/api/health` | 健康检查 |

## Agent 架构

```
START → router ──┬── tool_executor → router（ReAct 循环）
                 └── END（直接回答）
```

- **router**：LLM 判断用户意图，决定是否调用工具
- **tool_executor**：执行工具并返回结果
- 循环直到 LLM 认为信息足够，直接给出最终回答

## 技术栈

| 层 | 技术 |
|---|---|
| LLM | MiMo-V2.5-Pro（小米） |
| Agent 框架 | LangGraph |
| 后端 | FastAPI + Python |
| 前端 | Vue3 + TypeScript + Vite |
| UI 组件 | element-ai-vue + Element Plus |
| 钉钉接入 | dingtalk-stream（Stream 模式） |
| 记忆存储 | JSON 文件（按用户隔离） |

## 扩展工具

加新工具只需 3 步：

1. 在 `server/app/agent/tools/` 下新建文件，用 `@tool` 装饰器定义函数
2. 在 `server/app/agent/tools/__init__.py` 的 `ALL_TOOLS` 列表里注册
3. 在 `router.py` 的 System Prompt 里加一行工具描述

LLM 会自动根据描述决定什么时候使用新工具。
