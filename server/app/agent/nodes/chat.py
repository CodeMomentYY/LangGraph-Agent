"""
直接对话节点

这是最简单的节点：把对话历史发给 LLM，拿回回复。
不调工具、不做检索，就是纯聊天。

Phase 1 只有这一个节点，后续 Phase 会加 router / tool_executor / reflect。
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage

from app.config import get_settings
from app.agent.state import AgentState


# System Prompt：定义 Agent 的角色和行为
SYSTEM_PROMPT = """你是一个全能工作助手，名叫 MomentYY。你能帮用户做很多事情：
- 回答各种问题
- 帮忙写文案、周报、邮件
- 提供建议和分析

你的风格：简洁、专业、友好。不要啰嗦，直接给有用的信息。
如果用户的问题你不确定，诚实说明，不要编造。
"""


def get_llm() -> ChatOpenAI:
    """创建 LLM 实例"""
    settings = get_settings()
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=0.3,
    )


def chat_node(state: AgentState) -> dict:
    """
    直接对话节点。

    输入：state（包含完整对话历史）
    输出：{"messages": [新的 AI 回复]}

    LangGraph 会自动把返回的 messages 追加到 state.messages 末尾。
    """
    llm = get_llm()

    # 在对话历史前面加上 System Prompt
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(state["messages"])

    # 调用 LLM
    response = llm.invoke(messages)

    # 返回新消息（LangGraph 会自动追加到 state["messages"]）
    return {"messages": [response]}
