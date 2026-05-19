"""
配置管理模块

用 pydantic-settings 从 .env 文件加载配置。
好处：类型安全、有默认值、启动时就能发现配置缺失。
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置，自动从 .env 文件读取"""

    # LLM 配置
    llm_api_key: str
    llm_base_url: str
    llm_model: str

    # 服务配置
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # 钉钉配置
    dingtalk_client_id: str = ""
    dingtalk_client_secret: str = ""

    # 语雀配置
    yuque_api_token: str = ""
    yuque_base_url: str = "https://www.yuque.com/api/v2"
    dingtalk_client_secret: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """
    获取配置单例。
    @lru_cache 保证整个应用生命周期内只创建一次 Settings 实例。
    """
    return Settings()
