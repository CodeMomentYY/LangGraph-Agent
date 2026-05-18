"""
对话 API 接口（支持普通模式 + SSE 流式模式）
"""

import uuid
import json
from pydantic import BaseModel, Field
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage

from app.agent.graph import agent_app
from app.memory.conversation import load_history, save_history

router = APIRouter()


class ChatRequest(BaseModel):
    user_id: str = Field(default="default-user")
    message: str = Field(...)
    session_id: str = Field(default=None)


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    tools_used: list[str] = Field(default_factory=list)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """普通模式：一次性返回结果（钉钉机器人用这个）"""
    session_id = request.session_id or f"sess-{uuid.uuid4().hex[:8]}"
    history = load_history(session_id)
    all_messages = history + [HumanMessage(content=request.message)]

    initial_state = {
        "messages": all_messages,
        "user_id": request.user_id,
        "session_id": session_id,
        "intents": [],
        "mode": "sequential",
        "current_step": 0,
        "reflect_count": 0,
    }

    final_state = agent_app.invoke(initial_state)

    # 最后一条消息就是最终回复
    reply = final_state["messages"][-1].content or "抱歉，我无法生成回答。"

    # 保存历史
    history.append(HumanMessage(content=request.message))
    history.append(AIMessage(content=reply))
    save_history(session_id, history)

    # 收集工具
    tools_used = []
    for msg in final_state["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            tools_used.extend(tc["name"] for tc in msg.tool_calls)

    return ChatResponse(
        reply=reply,
        session_id=session_id,
        tools_used=list(set(tools_used)),
    )


# ============ SSE 流式接口（Web 前端用） ============

# 节点名称 → 用户友好的状态描述
NODE_STATUS_MAP = {
    "dispatcher": "🧠 正在分析你的问题，判断需要哪些能力来回答...",
    "mode_router": "",
    "step_router": "",
    "router": "💭 正在思考如何回答，判断是否需要查询外部信息...",
    "tool_executor": "⚡ 正在获取实时数据...",
    "writer_agent": "✍️ 正在为你撰写内容...",
    "chat_agent": "💬 正在组织回答...",
    "advance_step": "",
    "parallel_executor": "🔀 正在并行处理多个任务...",
}


def _stream_events(request: ChatRequest):
    """生成 SSE 事件流"""
    session_id = request.session_id or f"sess-{uuid.uuid4().hex[:8]}"
    history = load_history(session_id)
    all_messages = history + [HumanMessage(content=request.message)]

    initial_state = {
        "messages": all_messages,
        "user_id": request.user_id,
        "session_id": session_id,
        "intents": [],
        "mode": "sequential",
        "current_step": 0,
        "reflect_count": 0,
    }

    # 推送开始事件
    yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"

    # 收集所有消息用于最终提取回复
    all_output_messages = list(all_messages)
    tools_used = []

    # 使用 LangGraph 的 stream 逐节点执行
    for event in agent_app.stream(initial_state, stream_mode="updates"):
        for node_name, node_output in event.items():
            if node_output is None:
                node_output = {}

            # 推送节点执行状态（跳过空文案的内部节点）
            status = NODE_STATUS_MAP.get(node_name, "")
            if status:
                yield f"data: {json.dumps({'type': 'status', 'node': node_name, 'text': status})}\n\n"

            # 如果节点输出了意图信息
            if node_name == "dispatcher" and "intents" in node_output:
                intents = node_output["intents"]
                mode = node_output.get("mode", "sequential")
                mode_desc = "串行执行" if mode == "sequential" else "并行执行"
                intent_desc = " → ".join(intents)
                yield f"data: {json.dumps({'type': 'intents', 'intents': intents, 'mode': mode, 'text': f'识别到 {len(intents)} 个意图：{intent_desc}，将{mode_desc}'})}\n\n"

            # 如果节点输出了消息
            if "messages" in node_output:
                for msg in node_output["messages"]:
                    all_output_messages.append(msg)

                    # 推送 LLM 的思考过程（reasoning_content）
                    if hasattr(msg, "additional_kwargs") and msg.additional_kwargs.get("reasoning_content"):
                        reasoning = msg.additional_kwargs["reasoning_content"]
                        yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning})}\n\n"

                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        tc_names = [tc["name"] for tc in msg.tool_calls]
                        tc_args = [tc.get("args", {}) for tc in msg.tool_calls]
                        tools_used.extend(tc_names)
                        # 构建更详细的工具调用描述
                        tool_descs = []
                        for name, args in zip(tc_names, tc_args):
                            if name == "get_weather" and "city" in args:
                                tool_descs.append(f"查询 {args['city']} 的天气")
                            elif name == "recommend_activity" and "city" in args:
                                tool_descs.append(f"推荐 {args['city']} 的活动")
                            else:
                                tool_descs.append(f"调用 {name}")
                        yield f"data: {json.dumps({'type': 'tool_call', 'tools': tc_names, 'text': '、'.join(tool_descs)})}\n\n"
                    elif hasattr(msg, "content") and msg.content:
                        if hasattr(msg, "type") and msg.type == "tool":
                            yield f"data: {json.dumps({'type': 'tool_result', 'content': msg.content})}\n\n"

    # 提取最终回复（最后一条有内容的 AI 消息）
    reply = "抱歉，我无法生成回答。"
    for msg in reversed(all_output_messages):
        if hasattr(msg, "content") and msg.content:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                continue
            if hasattr(msg, "type") and msg.type == "tool":
                continue
            reply = msg.content
            break

    # 保存历史
    history.append(HumanMessage(content=request.message))
    history.append(AIMessage(content=reply))
    save_history(session_id, history)

    # 推送最终回复
    yield f"data: {json.dumps({'type': 'reply', 'content': reply, 'tools_used': list(set(tools_used)), 'session_id': session_id})}\n\n"

    # 推送结束
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """SSE 流式模式：逐步推送 Agent 执行过程（Web 前端用这个）"""
    return StreamingResponse(
        _stream_events(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
