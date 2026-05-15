"""
意图分发节点（Dispatcher）- 支持多意图

职责：判断用户意图，决定交给哪些专业 Agent 处理。
支持单意图和多意图（串行执行）。

意图类型：
  - weather: 天气查询、出行建议、景点推荐
  - writer: 写邮件、写周报、写文案、翻译
  - chat: 闲聊、知识问答、其他
"""

from langchain_core.messages import SystemMessage

from app.agent.state import AgentState
from app.agent.llm import invoke_llm


DISPATCHER_PROMPT = """你是一个意图分类器。根据用户的最新消息，判断应该交给哪些专业助手处理。

分类规则：
- weather：涉及天气、温度、出行、景点、推荐去哪玩、适不适合出门
- writer：涉及写作、写邮件、写周报、写文案、翻译、润色、总结文章
- chat：其他所有情况（闲聊、知识问答、自我介绍、计算等）

执行模式判断：
- 如果后一个任务需要前一个任务的结果，用 sequential（串行）
- 如果多个任务互相独立、互不依赖，用 parallel（并行）

回复格式（严格遵守，不要输出其他内容）：
意图1,意图2|模式

示例：
- "上海天气怎么样" → weather|sequential
- "帮我写封邮件" → writer|sequential
- "你好" → chat|sequential
- "查一下北京天气，写个朋友圈" → weather,writer|sequential
- "帮我翻译hello，顺便查一下上海天气" → weather,writer|parallel
- "北京天气和深圳天气分别怎么样" → weather|sequential
"""


def dispatcher_node(state: AgentState) -> dict:
    """
    分发节点：判断用户意图（支持多意图）。
    """
    # 取最后一条用户消息
    last_user_msg = ""
    for msg in reversed(state["messages"]):
        if hasattr(msg, "type") and msg.type == "human":
            last_user_msg = msg.content
            break
        elif hasattr(msg, "content") and not hasattr(msg, "tool_calls"):
            last_user_msg = msg.content
            break

    messages = [
        SystemMessage(content=DISPATCHER_PROMPT),
        SystemMessage(content=f"用户消息：{last_user_msg}"),
    ]

    response = invoke_llm(messages)
    raw = response.content.strip().lower()

    # 解析格式：intents|mode
    mode = "sequential"
    intent_part = raw

    if "|" in raw:
        parts = raw.split("|")
        intent_part = parts[0].strip()
        mode_raw = parts[1].strip()
        if mode_raw in ("sequential", "parallel"):
            mode = mode_raw

    # 解析多意图：按逗号分割
    valid_intents = {"weather", "writer", "chat"}
    intents = [i.strip() for i in intent_part.split(",") if i.strip() in valid_intents]

    # 兜底
    if not intents:
        intents = ["chat"]

    # 单意图不需要并行
    if len(intents) <= 1:
        mode = "sequential"

    return {"intents": intents, "current_step": 0, "mode": mode}
