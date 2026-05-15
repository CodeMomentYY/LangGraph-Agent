"""
写作专家 Agent

职责：处理所有写作类任务——邮件、周报、文案、翻译、润色、总结。
不带工具，纯 LLM 生成。temperature 设高一点（0.5）增加创造力。
"""

from langchain_core.messages import SystemMessage

from app.agent.state import AgentState
from app.agent.llm import invoke_llm


WRITER_PROMPT = """你是 MomentYY 的写作专家模块。你擅长：
- 撰写各类邮件（请假、商务、感谢信等）
- 撰写工作周报和日报
- 撰写产品文案和营销文案
- 翻译和润色文本
- 总结和提炼长文

写作风格：专业、简洁、有条理。
根据用户需求直接输出成品，不要问多余的问题。
如果用户没有提供足够信息，用合理的默认值填充。
"""


def writer_agent_node(state: AgentState) -> dict:
    """
    写作 Agent：直接调 LLM 生成写作内容。
    """
    messages = [SystemMessage(content=WRITER_PROMPT)] + list(state["messages"])
    response = invoke_llm(messages, temperature=0.5)
    return {"messages": [response]}
