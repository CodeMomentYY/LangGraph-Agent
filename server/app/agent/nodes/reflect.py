"""
反思节点（Reflection 范式）

审查 synthesize 节点生成的最终回答：
  - 如果质量够好 → 通过，走 END
  - 如果有问题 → 打回，让 synthesize 重写

通过在 state 里标记 reflection_pass 来控制条件边。
"""

from langchain_core.messages import SystemMessage, AIMessage

from app.agent.state import AgentState
from app.agent.llm import invoke_llm


REFLECT_PROMPT = """你是一个严格的质量审核员。审查下面的 AI 助手回复。

审查维度：
1. 是否准确回答了用户的问题？
2. 是否有事实性错误或自相矛盾？
3. 是否简洁有用（不啰嗦、不遗漏关键信息）？

评判标准：
- 如果回复质量达标（8分以上），只回复：✅ PASS
- 如果有明显问题，简述问题并回复：❌ REVISE: [具体问题]

只输出评判结果，不要重写回复。
"""


def reflect_node(state: AgentState) -> dict:
    """
    反思节点：审查最终回答的质量。

    把审查结果作为 AIMessage 加入 state。
    后续条件边会根据内容判断是 PASS 还是 REVISE。
    """
    # 取最后一条消息（synthesize 的输出）作为待审查对象
    last_reply = state["messages"][-1].content

    messages = [
        SystemMessage(content=REFLECT_PROMPT),
        SystemMessage(content=f"用户的原始问题：{state['messages'][0].content}"),
        SystemMessage(content=f"AI 助手的回复：\n{last_reply}"),
    ]

    response = invoke_llm(messages)

    # 把反思结果加入 state（用于条件边判断）
    return {"messages": [response]}
