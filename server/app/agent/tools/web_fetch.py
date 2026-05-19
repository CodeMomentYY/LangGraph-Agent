"""
网页内容获取工具

根据 URL 抓取网页内容，提取正文文本返回给 Agent。
支持语雀文档（通过 API + Token 认证获取）。
"""

import re
import requests
from langchain_core.tools import tool

from app.config import get_settings


def _fetch_yuque_doc(url: str) -> str:
    """通过语雀 API 获取文档内容（需要认证的语雀文档）"""
    settings = get_settings()
    token = getattr(settings, 'yuque_api_token', '')
    base_url = getattr(settings, 'yuque_base_url', 'https://www.yuque.com/api/v2')

    if not token:
        return "未配置 YUQUE_API_TOKEN，无法获取语雀文档"

    # 从 URL 提取 namespace 和 slug
    # 格式：https://xxx.yuque.com/group/book/doc_slug#anchor
    match = re.match(r'https?://[^/]+/([^/]+)/([^/]+)/([^#?]+)', url)
    if not match:
        return "无法解析语雀文档 URL"

    group, book, doc_slug = match.groups()
    namespace = f"{group}/{book}"

    # 调用语雀 API（强制不走代理）
    api_url = f"{base_url}/repos/{namespace}/docs/{doc_slug}"
    headers = {"X-Auth-Token": token}

    try:
        resp = requests.get(api_url, headers=headers, timeout=15, proxies={"http": None, "https": None})
        resp.raise_for_status()
        data = resp.json()

        doc = data.get("data", {})
        title = doc.get("title", "")
        body = doc.get("body", "") or doc.get("body_html", "")

        # 如果是 HTML 格式，简单去标签
        if "<" in body:
            body = re.sub(r'<[^>]+>', ' ', body)
            body = re.sub(r'\s+', ' ', body).strip()

        content = f"标题：{title}\n\n{body}"

        if len(content) > 4000:
            content = content[:4000] + "...(内容已截断)"

        return content

    except requests.RequestException as e:
        return f"获取语雀文档失败：{str(e)}"


def _fetch_normal_webpage(url: str) -> str:
    """普通网页抓取"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding

        html = resp.text

        # 移除 script 和 style 标签
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)

        # 移除所有 HTML 标签
        text = re.sub(r'<[^>]+>', ' ', html)

        # 清理多余空白
        text = re.sub(r'\s+', ' ', text).strip()

        if len(text) > 3000:
            text = text[:3000] + "...(内容已截断)"

        return text if text else "无法提取网页内容"

    except requests.Timeout:
        return "请求超时，网页无法访问"
    except requests.RequestException as e:
        return f"获取网页失败：{str(e)}"


@tool
def fetch_webpage(url: str) -> str:
    """获取指定网页的文本内容。支持普通网页和语雀文档。传入完整的 URL。"""
    # 判断是否是语雀 URL
    if 'yuque.com' in url:
        return _fetch_yuque_doc(url)
    else:
        return _fetch_normal_webpage(url)
