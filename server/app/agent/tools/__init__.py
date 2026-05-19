"""
工具注册表

所有工具在这里统一导出。
Agent 图里通过 import 这个列表来获取所有可用工具。
"""

from app.agent.tools.weather import get_weather
from app.agent.tools.recommend import recommend_activity
from app.agent.tools.web_fetch import fetch_webpage
from app.agent.tools.mcp_yuque import get_yuque_mcp_tools

# 所有可用工具的列表——加新工具只需要在这里多加一行
ALL_TOOLS = [
    get_weather,
    recommend_activity,
    fetch_webpage,
] + get_yuque_mcp_tools()
