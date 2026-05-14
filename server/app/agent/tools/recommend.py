"""
景点/活动推荐工具

内部再调一次 LLM（"LLM as a Tool" 模式），根据城市和天气推荐活动。
"""

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from app.config import get_settings


@tool
def recommend_activity(city: str, weather: str) -> str:
    """根据城市和当前天气推荐一个适合的活动或景点。当用户想知道去哪玩、做什么活动时使用。

    Args:
        city: 城市名称
        weather: 当前天气描述（建议传入 get_weather 的返回结果）
    """
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=0.7,
    )
    resp = llm.invoke(
        f"你是旅游达人。{city}现在{weather}，推荐 1 个最适合的活动或景点，50字内说明理由。"
    )
    return resp.content.strip()
