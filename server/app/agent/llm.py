"""
MiMo LLM 适配层

MiMo 的 thinking mode 会在 tool_calls 响应里返回 reasoning_content 字段，
并要求第二轮调用时传回去。LangChain 的 ChatOpenAI 不处理这个字段，
所以我们自己封装一层，用原生 OpenAI SDK 调用，再转成 LangChain 消息格式。

这就是"框架和特定模型不兼容时，自己写适配层"的典型场景。
"""

from openai import OpenAI
from langchain_core.messages import (
    BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
)

from app.config import get_settings


def _to_openai_messages(messages: list[BaseMessage]) -> list[dict]:
    """把 LangChain 消息转成 OpenAI API 格式，保留 reasoning_content"""
    result = []
    for msg in messages:
        if isinstance(msg, SystemMessage):
            result.append({"role": "system", "content": msg.content})
        elif isinstance(msg, HumanMessage):
            result.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            entry = {"role": "assistant", "content": msg.content or ""}
            # 保留 reasoning_content（MiMo 特殊要求）
            if hasattr(msg, "additional_kwargs") and msg.additional_kwargs.get("reasoning_content"):
                entry["reasoning_content"] = msg.additional_kwargs["reasoning_content"]
            # 保留 tool_calls
            if msg.tool_calls:
                import json as _json
                entry["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": _json.dumps(tc["args"], ensure_ascii=False) if isinstance(tc["args"], dict) else tc["args"],
                        },
                    }
                    for tc in msg.tool_calls
                ]
                # OpenAI 格式要求有 tool_calls 时 content 可以为空字符串
                if not entry["content"]:
                    entry["content"] = ""
            result.append(entry)
        elif isinstance(msg, ToolMessage):
            result.append({
                "role": "tool",
                "tool_call_id": msg.tool_call_id,
                "content": msg.content,
            })
    return result


def _to_langchain_message(openai_msg, raw_dict: dict) -> AIMessage:
    """把 OpenAI 响应转成 LangChain AIMessage，保留 reasoning_content"""
    tool_calls = []
    if openai_msg.tool_calls:
        import json
        for tc in openai_msg.tool_calls:
            tool_calls.append({
                "id": tc.id,
                "name": tc.function.name,
                "args": json.loads(tc.function.arguments) if tc.function.arguments else {},
            })

    additional_kwargs = {}
    # 保存 reasoning_content 到 additional_kwargs，下次传回去
    reasoning = raw_dict.get("reasoning_content", "")
    if reasoning:
        additional_kwargs["reasoning_content"] = reasoning

    return AIMessage(
        content=openai_msg.content or "",
        tool_calls=tool_calls,
        additional_kwargs=additional_kwargs,
    )


def invoke_llm(messages: list[BaseMessage], tools: list = None, temperature: float = 0) -> AIMessage:
    """
    调用 MiMo LLM，正确处理 reasoning_content。

    参数：
        messages: LangChain 格式的消息列表
        tools: 工具定义列表（OpenAI 格式的 JSON Schema）
        temperature: 生成温度，默认 0（精确），写作类可设 0.5

    返回：
        LangChain AIMessage（包含 tool_calls 和 reasoning_content）
    """
    settings = get_settings()
    client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)

    # 转成 OpenAI 格式
    openai_messages = _to_openai_messages(messages)

    # 构建请求参数
    kwargs = {
        "model": settings.llm_model,
        "messages": openai_messages,
        "temperature": temperature,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    # 调用
    resp = client.chat.completions.create(**kwargs)
    openai_msg = resp.choices[0].message

    # 转回 LangChain 格式（保留 reasoning_content）
    raw_dict = openai_msg.model_dump()
    return _to_langchain_message(openai_msg, raw_dict)
