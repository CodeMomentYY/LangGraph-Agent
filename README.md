# MomentYY Agent

多 Agent AI 助手，支持意图识别、串行/并行协作、SSE 流式输出。

## 特性

- 🧠 多 Agent 动态路由（天气 / 写作 / 聊天）
- 🔀 串行 + 并行执行模式
- ⚡ SSE 实时推送 Agent 执行过程
- 💭 LLM 思考过程可视化
- 🤖 钉钉机器人接入
- 🌗 日夜模式 + 代码高亮

## 技术栈

LangGraph · FastAPI · Vue3 · MiMo LLM · element-ai-vue · dingtalk-stream

## 快速开始

```bash
# 后端
cd server
cp .env.example .env          # 填入 API Key
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/uvicorn app.main:app --port 8000

# 前端
cd web
npm install && npm run dev    # http://localhost:3000

# 钉钉机器人（可选）
cd server
venv/bin/pip install dingtalk-stream
venv/bin/python -m app.dingtalk_bot
```

## 环境变量

```bash
# server/.env

# LLM 配置（必填）
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
LLM_MODEL=mimo-v2.5-pro

# 钉钉机器人（可选）
DINGTALK_CLIENT_ID=your-client-id
DINGTALK_CLIENT_SECRET=your-client-secret
```

## 架构

```
用户消息 → dispatcher（意图分类）
  ├── sequential: Agent1 → Agent2 → ... → END
  └── parallel:   Agent1 ∥ Agent2 → 整合 → END
```

## API

| 端点 | 说明 |
|------|------|
| `POST /api/chat` | 普通对话（钉钉用） |
| `POST /api/chat/stream` | SSE 流式对话（Web 用） |

## License

MIT
