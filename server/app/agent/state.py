"""
Agent 状态定义（Phase 3+：加入 reflection 计数器）
"""

from typing import Annotated, Sequence
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    """Agent 的全局状态"""

    # 对话历史（自动追加）
    messages: Annotated[Sequence[BaseMessage], operator.add]

    # 用户和会话标识
    user_id: str
    session_id: str

    # Reflection 计数器（防止无限循环）
    reflect_count: int
