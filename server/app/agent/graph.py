"""
LangGraph 图定义（简单模式：只有 router + tool_executor）

图结构：
    START → router ──┬── tool_executor → router（ReAct 循环）
                     └── END

去掉了 planner / synthesize / reflect，响应速度快 3-4 倍。
"""

from langgraph.graph import StateGraph, END

from app.agent.state import AgentState
from app.agent.nodes.router import router_node
from app.agent.nodes.tool_executor import tool_executor_node


def should_use_tools(state: AgentState) -> str:
    """router 之后：有 tool_calls → 执行工具；没有 → 结束"""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "end"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("router", router_node)
    graph.add_node("tool_executor", tool_executor_node)

    graph.set_entry_point("router")

    graph.add_conditional_edges(
        "router",
        should_use_tools,
        {
            "tools": "tool_executor",
            "end": END,
        },
    )

    graph.add_edge("tool_executor", "router")

    return graph.compile()


agent_app = build_graph()
