"""
LangGraph 图定义（多 Agent 架构 - 支持串行 + 并行）

执行模式：
  - sequential：按顺序逐个执行 Agent（有依赖关系）
  - parallel：在一个节点内并发执行多个 Agent，然后汇总（无依赖）

图结构：
    START → dispatcher → mode_router
        ├── sequential → step_router → Agent → advance_step → (循环或END)
        └── parallel → parallel_executor → END
"""

import asyncio
from langgraph.graph import StateGraph, END

from app.agent.state import AgentState
from app.agent.nodes.dispatcher import dispatcher_node
from app.agent.nodes.router import router_node
from app.agent.nodes.tool_executor import tool_executor_node
from app.agent.nodes.writer_agent import writer_agent_node
from app.agent.nodes.chat_agent import chat_agent_node
from app.agent.llm import invoke_llm

from langchain_core.messages import SystemMessage, AIMessage


# ============ 模式路由 ============

def mode_router_node(state: AgentState) -> dict:
    """空节点，纯做路由跳板"""
    return {}


def route_mode(state: AgentState) -> str:
    """根据 mode 决定走串行还是并行"""
    if state["mode"] == "parallel" and len(state["intents"]) > 1:
        return "parallel"
    return "sequential"


# ============ 串行模式 ============

def route_current_step(state: AgentState) -> str:
    """串行模式：根据当前 step 路由到对应 Agent"""
    step = state["current_step"]
    intents = state["intents"]
    if step < len(intents):
        return intents[step]
    return "done"


def should_use_tools(state: AgentState) -> str:
    """router 之后：有 tool_calls → 执行工具；没有 → 下一步"""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "next"


def has_next_step(state: AgentState) -> str:
    """串行模式：检查是否还有下一个意图"""
    step = state["current_step"]
    intents = state["intents"]
    if step + 1 < len(intents):
        return "continue"
    return "done"


def advance_step(state: AgentState) -> dict:
    """串行模式：推进到下一个意图"""
    return {"current_step": state["current_step"] + 1}


# ============ 并行模式 ============

def _execute_single_intent(intent: str, state: AgentState) -> str:
    """执行单个意图，返回文本结果"""
    if intent == "tools":
        # ReAct 循环（最多 5 轮）
        current_messages = list(state["messages"])
        result = router_node({**state, "messages": current_messages})
        current_messages = current_messages + result["messages"]

        for _ in range(5):
            last_msg = current_messages[-1]
            if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                temp_state = {**state, "messages": current_messages}
                tool_result = tool_executor_node(temp_state)
                current_messages = current_messages + tool_result["messages"]
                temp_state = {**state, "messages": current_messages}
                router_result = router_node(temp_state)
                current_messages = current_messages + router_result["messages"]
            else:
                break

        return current_messages[-1].content or ""

    elif intent == "writer":
        result = writer_agent_node(state)
        return result["messages"][0].content or ""

    else:  # chat
        result = chat_agent_node(state)
        return result["messages"][0].content or ""


def parallel_executor_node(state: AgentState) -> dict:
    """
    并行执行节点：用线程并发执行多个 Agent，然后汇总结果。
    """
    from concurrent.futures import ThreadPoolExecutor

    intents = state["intents"]

    # 并发执行所有意图
    with ThreadPoolExecutor(max_workers=len(intents)) as executor:
        futures = {
            intent: executor.submit(_execute_single_intent, intent, state)
            for intent in intents
        }
        results = {intent: f.result() for intent, f in futures.items()}

    # 如果只有一个结果，直接返回
    if len(results) == 1:
        reply = list(results.values())[0]
        return {"messages": [AIMessage(content=reply)]}

    # 多个结果，让 LLM 整合成一个连贯回答
    parts = "\n\n".join(
        f"【{intent} 结果】\n{content}" for intent, content in results.items()
    )
    merge_prompt = f"""请将以下多个助手的回复整合成一个连贯、自然的最终回答，保留所有关键信息：

{parts}

整合后的回答："""

    response = invoke_llm([SystemMessage(content=merge_prompt)])
    return {"messages": [response]}


# ============ 构建图 ============

def build_graph():
    graph = StateGraph(AgentState)

    # 注册节点
    graph.add_node("dispatcher", dispatcher_node)
    graph.add_node("mode_router", mode_router_node)
    graph.add_node("step_router", lambda state: {})
    graph.add_node("router", router_node)
    graph.add_node("tool_executor", tool_executor_node)
    graph.add_node("writer_agent", writer_agent_node)
    graph.add_node("chat_agent", chat_agent_node)
    graph.add_node("advance_step", advance_step)
    graph.add_node("parallel_executor", parallel_executor_node)

    # 入口
    graph.set_entry_point("dispatcher")

    # dispatcher → mode_router
    graph.add_edge("dispatcher", "mode_router")

    # mode_router → 根据 mode 分流
    graph.add_conditional_edges(
        "mode_router",
        route_mode,
        {
            "sequential": "step_router",
            "parallel": "parallel_executor",
        },
    )

    # ---- 串行路径 ----
    graph.add_conditional_edges(
        "step_router",
        route_current_step,
        {
            "tools": "router",
            "writer": "writer_agent",
            "chat": "chat_agent",
            "done": END,
        },
    )

    graph.add_conditional_edges(
        "router",
        should_use_tools,
        {
            "tools": "tool_executor",
            "next": "advance_step",
        },
    )
    graph.add_edge("tool_executor", "router")
    graph.add_edge("writer_agent", "advance_step")
    graph.add_edge("chat_agent", "advance_step")

    graph.add_conditional_edges(
        "advance_step",
        has_next_step,
        {
            "continue": "step_router",
            "done": END,
        },
    )

    # ---- 并行路径 ----
    graph.add_edge("parallel_executor", END)

    return graph.compile()


agent_app = build_graph()
