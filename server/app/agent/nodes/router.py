"""
路由节点（Phase 2）

让 LLM 判断用户意图，决定走哪条路：
- 需要工具 → 返回 tool_calls → 后续走 tool_executor
- 不需要工具 → 直接返回文本回复 → 后续走 END

使用自定义的 llm.py 适配层来处理 MiMo 的 reasoning_content。
"""

from langchain_core.messages import SystemMessage

from app.agent.state import AgentState
from app.agent.llm import invoke_llm
from app.agent.tools import ALL_TOOLS


SYSTEM_PROMPT = """你是一个全能工作助手，名叫 MomentYY。

你有以下工具可以使用：
- get_weather: 查询城市实时天气
- recommend_activity: 根据城市和天气推荐活动/景点
- fetch_webpage: 获取普通网页的文本内容（非语雀链接使用）
- get_doc: 获取语雀文档内容（如果链接包含 yuque.com，优先使用此工具。参数：namespace 格式为 "group/book"，slug 为文档ID）
- search_docs: 搜索语雀文档（参数：query 搜索关键词）
- list_docs: 获取语雀知识库下的文档列表（参数：namespace 格式为 "group/book"）

规则：
1. 如果用户的问题需要实时信息（天气、时间等），使用对应工具
2. 如果用户想要推荐（景点、活动），先查天气再推荐
3. 如果用户提供了语雀链接（包含 yuque.com），使用 get_doc 工具，从URL中提取 namespace 和 slug（如 https://xxx.yuque.com/aaa/bbb/ccc → namespace="aaa/bbb", slug="ccc"）
4. 如果用户提供了其他网页链接，使用 fetch_webpage 工具
5. 如果用户要搜索语雀文档，使用 search_docs 工具
6. 如果是普通闲聊或知识问答，直接回答，不要调用工具
7. 回答风格：简洁、专业、友好
"""


def _get_tool_schemas() -> list[dict]:
    """把 LangChain @tool 转成 OpenAI tools 格式"""
    schemas = []
    for t in ALL_TOOLS:
        # args_schema 可能是 Pydantic model 或 dict（MCP 工具）
        if t.args_schema:
            if isinstance(t.args_schema, dict):
                params = t.args_schema
            else:
                params = t.args_schema.schema()
        else:
            params = {"type": "object", "properties": {}}

        schema = {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": params,
            },
        }
        schemas.append(schema)
    return schemas


TOOL_SCHEMAS = _get_tool_schemas()


def router_node(state: AgentState) -> dict:
    """
    路由节点：让 LLM 决定是直接回答还是调用工具。
    """
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(state["messages"])
    response = invoke_llm(messages, tools=TOOL_SCHEMAS)
    return {"messages": [response]}
