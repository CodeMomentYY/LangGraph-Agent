"""
天气查询工具

调用 wttr.in 公开 API 获取实时天气。
这个工具用 @tool 装饰器定义，LangGraph 能自动识别并注册。
"""

import requests
from urllib.parse import quote
from langchain_core.tools import tool


@tool
def get_weather(city: str) -> str:
    """查询指定城市的实时天气。当用户询问天气、温度、是否下雨、能不能出门等问题时使用。

    Args:
        city: 城市名称，例如"北京"、"上海"
    """
    try:
        url = f"https://wttr.in/{quote(city)}?format=j1&lang=zh"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        cur = data["current_condition"][0]
        desc = (cur.get("lang_zh") or cur.get("weatherDesc"))[0]["value"]
        return f"{city}天气：{desc}，气温 {cur['temp_C']}°C，湿度 {cur['humidity']}%"
    except requests.exceptions.RequestException as e:
        return f"查询{city}天气失败（网络问题）：{e}"
    except (KeyError, IndexError, ValueError) as e:
        return f"查询{city}天气失败（数据解析问题）：{e}"
