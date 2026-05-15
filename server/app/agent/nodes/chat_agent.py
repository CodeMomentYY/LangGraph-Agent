"""
通用聊天 Agent

职责：处理闲聊、知识问答、自我介绍等不需要工具的对话。
纯 LLM 生成，温度保持默认（0），回答准确优先。
"""

from langchain_core.messages import SystemMessage

from app.agent.state import AgentState
from app.agent.llm import invoke_llm


CHAT_PROMPT = """你是 MomentYY，一个友好、专业的 AI 助手。

你的特点：
- 回答简洁清晰，不啰嗦
- 语气温和友好，像朋友聊天
- 遇到不确定的问题会坦诚说明
- 支持中英文对话

直接回答用户的问题，不要使用任何工具。
"""


def chat_agent_node(state: AgentState) -> dict:
    """
    聊天 Agent：直接调 LLM 回答。
    """
    messages = [SystemMessage(content=CHAT_PROMPT)] + list(state["messages"])
    response = invoke_llm(messages)
    return {"messages": [response]}
