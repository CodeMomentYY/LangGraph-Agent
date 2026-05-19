"""
工具执行节点

当 router 节点决定调用工具时，这个节点负责真正执行工具。

工作方式：
  1. 从 state 最后一条消息里取出 tool_calls
  2. 逐个执行对应的工具函数
  3. 把工具结果作为 ToolMessage 返回

执行完后，控制流会回到 router 节点，让 LLM 看到工具结果后决定下一步。
"""

from langchain_core.messages import ToolMessage

from app.agent.state import AgentState
from app.agent.tools import ALL_TOOLS


# 构建工具名 → 工具函数的映射
TOOL_MAP = {t.name: t for t in ALL_TOOLS}


def tool_executor_node(state: AgentState) -> dict:
    """
    执行工具并返回结果。

    从最后一条 AI 消息的 tool_calls 里取出要调用的工具，
    逐个执行，把结果包装成 ToolMessage 返回。
    """
    # 最后一条消息是 router 节点返回的（包含 tool_calls）
    last_message = state["messages"][-1]
    tool_calls = last_message.tool_calls

    results = []
    for tc in tool_calls:
        tool_name = tc["name"]
        tool_args = tc["args"]

        # 找到对应的工具函数并执行
        tool_fn = TOOL_MAP.get(tool_name)
        if tool_fn:
            # MCP 工具是异步的，需要用 asyncio.run 调用
            if hasattr(tool_fn, 'coroutine') and tool_fn.coroutine:
                import asyncio
                result = asyncio.run(tool_fn.ainvoke(tool_args))
            else:
                result = tool_fn.invoke(tool_args)
        else:
            result = f"未知工具: {tool_name}"

        # 包装成 ToolMessage（必须带 tool_call_id，LLM 才能对应上）
        results.append(
            ToolMessage(content=str(result), tool_call_id=tc["id"])
        )

    return {"messages": results}
