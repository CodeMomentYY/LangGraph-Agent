"""
向量记忆存储（RAG 长期记忆）

使用 ChromaDB 存储对话历史的向量表示，支持语义检索。
每轮对话（user + ai）作为一条记录存入向量库。
检索时根据当前问题找到最相关的历史对话。
"""

import time
import chromadb
from pathlib import Path


# ChromaDB 持久化目录
CHROMA_PATH = Path(__file__).parent.parent.parent / "data" / "chroma"
CHROMA_PATH.mkdir(parents=True, exist_ok=True)

# 全局客户端（单例）
_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
_collection = _client.get_or_create_collection(
    name="conversations",
    metadata={"hnsw:space": "cosine"},
)


def save_conversation(session_id: str, user_message: str, ai_reply: str):
    """
    保存一轮对话到向量库。

    将 user_message + ai_reply 拼接为一条文档存入，
    ChromaDB 会自动用内置 embedding 模型生成向量。
    """
    doc = f"用户：{user_message}\n助手：{ai_reply}"
    doc_id = f"{session_id}_{int(time.time() * 1000)}"

    _collection.add(
        documents=[doc],
        metadatas=[{
            "session_id": session_id,
            "user_message": user_message[:200],
            "timestamp": str(int(time.time())),
        }],
        ids=[doc_id],
    )


def search_relevant(query: str, top_k: int = 3, session_id: str = None) -> list[str]:
    """
    根据当前问题检索相关的知识和历史对话。
    优先检索知识库（session_id='knowledge'），再补充对话历史。
    """
    if _collection.count() == 0:
        return []

    results_with_score = []

    try:
        all_data = _collection.get(include=["documents", "metadatas"])
        if all_data and all_data.get("documents"):
            query_terms = _extract_terms(query)
            for doc, meta in zip(all_data["documents"], all_data["metadatas"]):
                score = 0
                doc_lower = doc.lower()
                for term in query_terms:
                    if term in doc_lower:
                        score += len(term)
                if score > 0:
                    # 知识库内容加权（优先级更高）
                    if meta and meta.get("session_id") == "knowledge":
                        score *= 3
                    results_with_score.append((score, doc))
    except Exception:
        pass

    results_with_score.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in results_with_score[:top_k]]


def _extract_terms(text: str) -> list[str]:
    """从文本中提取检索词（2-4字的滑动窗口 + 完整词）"""
    # 去掉标点和空格
    clean = ''.join(c for c in text if c.isalnum() or c in '的了吗呢是')
    terms = set()

    # 滑动窗口：2字、3字、4字
    for size in [2, 3, 4]:
        for i in range(len(clean) - size + 1):
            term = clean[i:i+size]
            # 过滤掉纯停用词
            if term not in ('的了', '了吗', '吗呢', '是的', '你了', '我的'):
                terms.add(term)

    # 也加入原始 query 中的英文单词
    import re
    english_words = re.findall(r'[a-zA-Z]+', text)
    for w in english_words:
        if len(w) >= 2:
            terms.add(w.lower())

    return list(terms)
