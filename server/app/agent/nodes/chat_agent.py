"""
通用聊天 Agent（带 RAG 长期记忆）

职责：处理闲聊、知识问答、自我介绍等不需要工具的对话。
会从向量库检索相关历史对话，让 Agent 能"回忆"之前聊过的内容。
"""

from langchain_core.messages import SystemMessage

from app.agent.state import AgentState
from app.agent.llm import invoke_llm
from app.memory.vector_store import search_relevant


CHAT_PROMPT = """你是 MomentYY，一个友好、专业的 AI 助手。

你的特点：
- 回答简洁清晰，不啰嗦
- 语气温和友好，像朋友聊天
- 遇到不确定的问题会坦诚说明
- 支持中英文对话
- 能够记住之前和用户聊过的内容

直接回答用户的问题，不要使用任何工具。
"""


def chat_agent_node(state: AgentState) -> dict:
    """
    聊天 Agent：检索相关历史 + 调 LLM 回答。
    """
    # 取最后一条用户消息用于 RAG 检索
    last_user_msg = ""
    for msg in reversed(state["messages"]):
        if hasattr(msg, "type") and msg.type == "human":
            last_user_msg = msg.content
            break

    # RAG 检索相关历史对话
    prompt = CHAT_PROMPT
    if last_user_msg:
        relevant = search_relevant(last_user_msg, top_k=3)
        if relevant:
            memory_context = "\n\n".join(relevant)
            prompt += f"\n\n【重要】以下是相关的参考资料和历史对话，请优先基于这些内容回答：\n\n{memory_context}\n\n请基于以上资料回答用户的问题，如果资料中有相关信息，直接引用具体内容回答。"

    messages = [SystemMessage(content=prompt)] + list(state["messages"])
    response = invoke_llm(messages)
    return {"messages": [response]}
