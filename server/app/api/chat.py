"""
对话 API 接口（简单模式）
"""

import uuid
from pydantic import BaseModel, Field
from fastapi import APIRouter
from langchain_core.messages import HumanMessage, AIMessage

from app.agent.graph import agent_app
from app.memory.conversation import load_history, save_history

router = APIRouter()


class ChatRequest(BaseModel):
    user_id: str = Field(default="default-user")
    message: str = Field(...)
    session_id: str = Field(default=None)


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    tools_used: list[str] = Field(default_factory=list)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id or f"sess-{uuid.uuid4().hex[:8]}"
    history = load_history(session_id)
    all_messages = history + [HumanMessage(content=request.message)]

    initial_state = {
        "messages": all_messages,
        "user_id": request.user_id,
        "session_id": session_id,
        "reflect_count": 0,
    }

    final_state = agent_app.invoke(initial_state)

    # 最后一条消息就是最终回复
    reply = final_state["messages"][-1].content or "抱歉，我无法生成回答。"

    # 保存历史
    history.append(HumanMessage(content=request.message))
    history.append(AIMessage(content=reply))
    save_history(session_id, history)

    # 收集工具
    tools_used = []
    for msg in final_state["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            tools_used.extend(tc["name"] for tc in msg.tool_calls)

    return ChatResponse(
        reply=reply,
        session_id=session_id,
        tools_used=list(set(tools_used)),
    )
