"""
钉钉机器人（Stream 模式）

Stream 模式的优势：
  - 不需要公网地址
  - 客户端主动连接钉钉服务器（长连接）
  - 适合本地开发和内网部署

使用方式：
  python -m app.dingtalk_bot
"""

import asyncio
import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from langchain_core.messages import HumanMessage, AIMessage

import dingtalk_stream
from dingtalk_stream import AckMessage
from dingtalk_stream.chatbot import ChatbotMessage

from app.config import get_settings
from app.agent.graph import agent_app
from app.memory.conversation import load_history, save_history

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 线程池：用于在线程中执行同步的 agent_app.invoke()
_executor = ThreadPoolExecutor(max_workers=4)


class MomentYYBotHandler(dingtalk_stream.ChatbotHandler):
    """
    钉钉消息处理器
    """

    def __init__(self):
        super().__init__()
        self._processed_ids = set()
        self._dedup_lock = asyncio.Lock()
        # 每个 session 一把锁，保证同一 session 内消息串行处理
        self._session_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def process(self, callback: dingtalk_stream.CallbackMessage):
        incoming_message = ChatbotMessage.from_dict(callback.data)

        # 去重
        msg_id = incoming_message.message_id
        async with self._dedup_lock:
            if msg_id in self._processed_ids:
                return AckMessage.STATUS_OK, "OK"
            self._processed_ids.add(msg_id)
            if len(self._processed_ids) > 200:
                self._processed_ids = set(list(self._processed_ids)[-100:])

        user_id = incoming_message.sender_id
        text = incoming_message.text.content.strip()

        conversation_type = incoming_message.conversation_type
        conversation_id = incoming_message.conversation_id
        is_group = (conversation_type == '2')

        if is_group:
            session_id = f"dingtalk-group-{conversation_id}"
        else:
            session_id = f"dingtalk-{user_id}"

        sender_nick = incoming_message.sender_nick or user_id

        logger.info(f"收到消息 [{sender_nick}] ({'群聊' if is_group else '私聊'}): {text}")

        # 同一 session 串行处理，避免历史记录竞态
        async with self._session_locks[session_id]:
            reply = await self._handle_message(
                session_id, user_id, sender_nick, text, is_group
            )

        self.reply_markdown("MomentYY", reply, incoming_message)
        return AckMessage.STATUS_OK, "OK"

    async def _handle_message(
        self, session_id: str, user_id: str, sender_nick: str, text: str, is_group: bool
    ) -> str:
        try:
            history = load_history(session_id)

            user_msg = f"[{sender_nick}]: {text}" if is_group else text
            all_messages = history + [HumanMessage(content=user_msg)]

            initial_state = {
                "messages": all_messages,
                "user_id": user_id,
                "session_id": session_id,
                "intents": [],
                "mode": "sequential",
                "current_step": 0,
                "reflect_count": 0,
            }

            # 在线程池中执行同步的 invoke，不阻塞事件循环
            loop = asyncio.get_event_loop()
            final_state = await loop.run_in_executor(
                _executor, agent_app.invoke, initial_state
            )

            # 提取回复
            reply = ""
            for msg in reversed(final_state["messages"]):
                if hasattr(msg, "content") and msg.content:
                    if hasattr(msg, "type") and msg.type == "human":
                        continue
                    if "<tool_call>" in msg.content or "<function=" in msg.content:
                        continue
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        continue
                    reply = msg.content
                    break

            if not reply:
                reply = "抱歉，我暂时无法回答这个问题。"

            # 保存历史
            history.append(HumanMessage(content=user_msg))
            history.append(AIMessage(content=reply))
            save_history(session_id, history)

            logger.info(f"回复 [{user_id}]: {reply[:50]}...")
            return reply

        except Exception as e:
            logger.error(f"处理消息出错: {e}")
            return "我刚刚走神了，再说一次吧 🫠"


def start_dingtalk_bot():
    """启动钉钉机器人（阻塞运行）"""
    settings = get_settings()

    if not settings.dingtalk_client_id or not settings.dingtalk_client_secret:
        logger.error("未配置 DINGTALK_CLIENT_ID 或 DINGTALK_CLIENT_SECRET")
        return

    credential = dingtalk_stream.Credential(
        settings.dingtalk_client_id,
        settings.dingtalk_client_secret,
    )

    client = dingtalk_stream.DingTalkStreamClient(credential)
    client.register_callback_handler(
        dingtalk_stream.chatbot.ChatbotMessage.TOPIC,
        MomentYYBotHandler(),
    )

    logger.info(f"🤖 钉钉机器人启动中... (Client ID: {settings.dingtalk_client_id})")
    client.start_forever()


if __name__ == "__main__":
    start_dingtalk_bot()
