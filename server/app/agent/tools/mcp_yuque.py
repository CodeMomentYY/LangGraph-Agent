"""
语雀 MCP 工具接入

通过 langchain-mcp-adapters 连接语雀 MCP 服务器，
将 MCP 工具转为 LangChain Tool 格式注册到 Agent。
"""

import asyncio
import logging
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)

# 全局缓存：MCP 工具列表
_mcp_tools: Optional[list] = None


def _load_mcp_tools_sync() -> list:
    """同步方式加载 MCP 工具（内部用 asyncio.run）"""
    settings = get_settings()

    if not settings.yuque_api_token:
        logger.warning("未配置 YUQUE_API_TOKEN，跳过语雀 MCP 加载")
        return []

    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient

        async def _load():
            client = MultiServerMCPClient({
                'yuque': {
                    'transport': 'stdio',
                    'command': 'npx',
                    'args': ['-y', '@momentyy/yuque-mcp-server'],
                    'env': {
                        'YUQUE_API_TOKEN': settings.yuque_api_token,
                        'YUQUE_BASE_URL': settings.yuque_base_url,
                    },
                }
            })
            return await client.get_tools()

        tools = asyncio.run(_load())
        logger.info(f"✅ 语雀 MCP 加载成功，获取到 {len(tools)} 个工具")
        return tools

    except Exception as e:
        logger.error(f"❌ 语雀 MCP 加载失败: {e}")
        return []


def get_yuque_mcp_tools() -> list:
    """获取语雀 MCP 工具列表（带缓存）"""
    global _mcp_tools
    if _mcp_tools is None:
        _mcp_tools = _load_mcp_tools_sync()
    return _mcp_tools
