"""
规划节点（Plan-and-Solve 的 Plan 阶段）

判断任务是否复杂：
  - 简单任务（闲聊、单步查询）→ 跳过规划，直接进 router
  - 复杂任务（多步骤、需要对比、需要综合）→ 生成计划，写入 state

通过在 state 里设置 plan 字段来传递计划。
"""

from langchain_core.messages import SystemMessage, AIMessage

from app.agent.state import AgentState
from app.agent.llm import invoke_llm


PLANNER_PROMPT = """你是一个任务规划专家。判断用户的请求是否需要多步骤完成。

规则：
1. 如果是简单问题（闲聊、单个查询、直接能答的），回复：SIMPLE
2. 如果是复杂任务（需要多步骤、对比、综合分析），回复一个简短的计划，格式如下：

PLAN:
1. 第一步
2. 第二步
3. 第三步

只输出 SIMPLE 或 PLAN，不要其他内容。
"""


def planner_node(state: AgentState) -> dict:
    """
    规划节点：判断任务复杂度，复杂任务生成计划。

    计划信息通过 AIMessage 传递（内容以 PLAN: 开头），
    后续 router 节点会看到这个计划并据此行动。
    """
    messages = [SystemMessage(content=PLANNER_PROMPT)] + list(state["messages"])
    response = invoke_llm(messages)

    # 如果是简单任务，不加任何消息（直接进 router）
    if "SIMPLE" in response.content.upper():
        return {"messages": []}

    # 复杂任务：把计划作为系统提示加入，引导后续 router 按计划执行
    plan_msg = AIMessage(
        content=f"[内部计划] {response.content}\n请按照以上计划逐步执行。"
    )
    return {"messages": [plan_msg]}
