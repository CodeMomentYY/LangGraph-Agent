"""
Agent 状态定义（多 Agent 架构 - 支持多意图串行）

intent 改为列表：dispatcher 可返回多个意图，按顺序执行。
current_step 追踪当前执行到第几个意图。
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

    # 意图列表（dispatcher 填写，支持多意图串行/并行）
    intents: list[str]

    # 执行模式：sequential（串行，有依赖）或 parallel（并行，无依赖）
    mode: str

    # 当前执行到第几个意图（0-indexed，仅串行模式使用）
    current_step: int

    # Reflection 计数器（保留兼容）
    reflect_count: int
