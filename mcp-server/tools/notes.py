"""Notes CRUD tools with FTS5 full-text search."""
from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

from db import get_conn


def register(mcp: "FastMCP") -> None:

    @mcp.tool()
    def note_create(
        title: str,
        content: str = "",
        tags: list[str] = [],
    ) -> dict:
        """创建笔记。"""
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO notes (title, content, tags) VALUES (?,?,?)",
                (title, content, json.dumps(tags, ensure_ascii=False)),
            )
            return {"id": cur.lastrowid, "title": title}

    @mcp.tool()
    def note_list(limit: int = 20) -> list[dict]:
        """列出最近的笔记，按创建时间倒序。"""
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT id, title, tags, created_at FROM notes ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    @mcp.tool()
    def note_search(query: str, limit: int = 10) -> list[dict]:
        """全文搜索笔记（FTS5），支持模糊匹配。"""
        with get_conn() as conn:
            rows = conn.execute(
                """SELECT n.* FROM notes n
                   JOIN notes_fts f ON n.id = f.rowid
                   WHERE notes_fts MATCH ?
                   ORDER BY rank LIMIT ?""",
                (query, limit),
            ).fetchall()
            return [dict(r) for r in rows]

    @mcp.tool()
    def note_update(
        id: int,
        title: str = "",
        content: str = "",
        tags: list[str] = [],
    ) -> dict:
        """更新笔记字段，只传需要修改的字段。"""
        fields, params = [], []
        if title:   fields.append("title=?");   params.append(title)
        if content: fields.append("content=?"); params.append(content)
        if tags:    fields.append("tags=?");    params.append(json.dumps(tags, ensure_ascii=False))
        if not fields:
            return {"error": "no fields provided"}
        fields.append("updated_at=?")
        params.append(datetime.now().isoformat(timespec="seconds"))
        params.append(id)
        with get_conn() as conn:
            conn.execute(f"UPDATE notes SET {', '.join(fields)} WHERE id=?", params)
            return {"id": id, "updated": True}

    @mcp.tool()
    def note_delete(id: int) -> dict:
        """删除笔记。"""
        with get_conn() as conn:
            conn.execute("DELETE FROM notes WHERE id=?", (id,))
            return {"id": id, "deleted": True}
