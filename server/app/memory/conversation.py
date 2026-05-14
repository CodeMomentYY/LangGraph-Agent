"""
对话历史管理

用 JSON 文件持久化每个 session 的对话历史。
生产级会用 Redis / PostgreSQL，但学习阶段 JSON 文件最直观。

核心逻辑：
  - 每个 session_id 对应一个 JSON 文件
  - 文件里存的是 messages 列表（序列化后的 LangChain 消息）
  - 每次请求前：加载历史 → 拼到 state 里
  - 每次请求后：把新消息追加保存
"""

import os
import json
from typing import Optional
from langchain_core.messages import (
    BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
)

# 存储目录
MEMORY_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "memory")


def _get_session_file(session_id: str) -> str:
    """获取某个 session 的存储文件路径"""
    os.makedirs(MEMORY_DIR, exist_ok=True)
    # 把特殊字符替换掉，避免文件名非法
    safe_name = session_id.replace("/", "_").replace(":", "_").replace("$", "_").replace(" ", "_")
    return os.path.join(MEMORY_DIR, f"{safe_name}.json")


def _serialize_message(msg: BaseMessage) -> dict:
    """把 LangChain 消息序列化成可存储的 dict"""
    data = {
        "type": type(msg).__name__,
        "content": msg.content,
    }
    if isinstance(msg, AIMessage) and msg.tool_calls:
        data["tool_calls"] = msg.tool_calls
    if isinstance(msg, AIMessage) and msg.additional_kwargs.get("reasoning_content"):
        data["reasoning_content"] = msg.additional_kwargs["reasoning_content"]
    if isinstance(msg, ToolMessage):
        data["tool_call_id"] = msg.tool_call_id
    return data


def _deserialize_message(data: dict) -> Optional[BaseMessage]:
    """把存储的 dict 还原成 LangChain 消息"""
    msg_type = data["type"]
    content = data.get("content", "")

    if msg_type == "HumanMessage":
        return HumanMessage(content=content)
    elif msg_type == "AIMessage":
        kwargs = {}
        if data.get("reasoning_content"):
            kwargs["additional_kwargs"] = {"reasoning_content": data["reasoning_content"]}
        return AIMessage(
            content=content,
            tool_calls=data.get("tool_calls", []),
            **kwargs,
        )
    elif msg_type == "ToolMessage":
        return ToolMessage(content=content, tool_call_id=data.get("tool_call_id", ""))
    elif msg_type == "SystemMessage":
        return SystemMessage(content=content)
    return None


def load_history(session_id: str) -> list[BaseMessage]:
    """加载某个 session 的对话历史"""
    file_path = _get_session_file(session_id)
    if not os.path.exists(file_path):
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        data_list = json.load(f)

    messages = []
    for data in data_list:
        msg = _deserialize_message(data)
        if msg:
            messages.append(msg)
    return messages


def save_history(session_id: str, messages: list[BaseMessage]):
    """保存对话历史（覆盖写入）"""
    file_path = _get_session_file(session_id)
    data_list = [_serialize_message(msg) for msg in messages]

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data_list, f, ensure_ascii=False, indent=2)


def clear_history(session_id: str):
    """清除某个 session 的对话历史"""
    file_path = _get_session_file(session_id)
    if os.path.exists(file_path):
        os.remove(file_path)
