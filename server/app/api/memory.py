"""
记忆管理 API

GET /api/memory/{session_id}    查看对话历史
DELETE /api/memory/{session_id}  清除对话历史
"""

from fastapi import APIRouter
from app.memory.conversation import load_history, clear_history

router = APIRouter()


@router.get("/memory/{session_id}")
async def get_memory(session_id: str):
    """查看某个 session 的对话历史"""
    history = load_history(session_id)
    messages = [
        {"role": type(msg).__name__, "content": msg.content}
        for msg in history
    ]
    return {"session_id": session_id, "message_count": len(messages), "messages": messages}


@router.delete("/memory/{session_id}")
async def delete_memory(session_id: str):
    """清除某个 session 的对话历史"""
    clear_history(session_id)
    return {"status": "ok", "message": f"Session {session_id} 的记忆已清除"}
