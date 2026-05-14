"""
综合回答节点

当 router 决定不再调工具时（走 END 路径），先经过这个节点：
把所有工具结果综合成一个完整、流畅的最终回答。

为什么需要这个节点？
  - router 最后一轮的回答可能比较简短
  - 有了 synthesize，可以把所有中间结果整合成高质量的最终回复
  - 也为 Reflection 提供了一个明确的"待审查对象"
"""

from langchain_core.messages import SystemMessage, AIMessage

from app.agent.state import AgentState
from app.agent.llm import invoke_llm


SYNTHESIZE_PROMPT = """你是 MomentYY，一个全能工作助手。
请根据对话历史中收集到的所有信息，给用户一个完整、简洁、有用的最终回答。

要求：
- 综合所有工具返回的信息
- 语言自然流畅，不要罗列原始数据
- 如果有推荐，给出具体理由
- 控制在 200 字以内
"""


def synthesize_node(state: AgentState) -> dict:
    """综合所有信息生成最终回答"""
    messages = [SystemMessage(content=SYNTHESIZE_PROMPT)] + list(state["messages"])
    response = invoke_llm(messages)
    return {"messages": [response]}
