"""Long-term semantic memory tools powered by mem0."""
from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

_memory = None
_USER_ID = "user"


def _get_memory():
    global _memory
    if _memory is not None:
        return _memory

    from mem0 import Memory

    _api_key = os.getenv("MEM0_API_KEY") or os.getenv("DEFAULT_API_KEY") or os.getenv("OPENAI_API_KEY", "")
    _api_base = os.getenv("MEM0_API_BASE") or os.getenv("DEFAULT_API_BASE") or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    store_path = os.environ.get("DATA_DIR")
    if store_path:
        store_path = str(Path(store_path) / "memory_store")
    else:
        store_path = str(Path(__file__).parent.parent / "memory_store")
    config = {
        "llm": {
            "provider": "openai",
            "config": {
                "model": os.getenv("MEM0_MODEL", "gpt-4o-mini"),
                "api_key": _api_key,
                "openai_base_url": _api_base,
            },
        },
        "embedder": {
            "provider": "openai",
            "config": {
                "model": os.getenv("MEM0_EMBED_MODEL", "text-embedding-3-small"),
                "api_key": _api_key,
                "openai_base_url": _api_base,
            },
        },
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "collection_name": "life-assistant",
                "path": store_path,
            },
        },
        "custom_instructions": "请用中文（简体）提取并存储记忆事实。",
    }
    _memory = Memory.from_config(config)
    return _memory


def register(mcp: "FastMCP") -> None:

    @mcp.tool()
    def memory_add(content: str) -> dict:
        """存储一条长期记忆（用户偏好、重要事实、个人信息等）。
        mem0 会自动去重并合并与已有记忆冲突的内容。
        示例：memory_add("用户不喜欢早起，习惯晚上12点睡觉")
        """
        result = _get_memory().add(content, user_id=_USER_ID)
        return {"stored": True, "result": result}

    @mcp.tool()
    def memory_search(query: str, limit: int = 5) -> list[dict]:
        """按语义相似度检索相关记忆。
        示例：memory_search("用户的作息习惯")
        """
        results = _get_memory().search(query, user_id=_USER_ID, limit=limit)
        memories = results.get("results", results) if isinstance(results, dict) else results
        return [{"id": m.get("id", ""), "memory": m.get("memory", str(m))} for m in memories]

    @mcp.tool()
    def memory_get_all() -> list[dict]:
        """获取全部已存储的长期记忆。"""
        results = _get_memory().get_all(user_id=_USER_ID)
        memories = results.get("results", results) if isinstance(results, dict) else results
        return [{"id": m.get("id", ""), "memory": m.get("memory", str(m))} for m in memories]

    @mcp.tool()
    def memory_delete(id: str) -> dict:
        """按 ID 删除指定记忆。"""
        _get_memory().delete(id)
        return {"id": id, "deleted": True}
