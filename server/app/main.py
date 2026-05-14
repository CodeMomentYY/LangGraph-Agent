"""
FastAPI 应用主入口（Phase 3）

新增：/api/memory 路由
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.api.memory import router as memory_router

app = FastAPI(
    title="MomentYY Agent Server",
    description="基于 LangGraph 的全能工作助手 API",
    version="0.3.0",
)

# CORS 配置（允许前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat_router, prefix="/api", tags=["对话"])
app.include_router(memory_router, prefix="/api", tags=["记忆"])


@app.get("/api/health", tags=["系统"])
async def health_check():
    return {"status": "ok", "version": "0.3.0"}
