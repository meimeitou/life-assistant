"""Task CRUD tools."""
from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

from db import get_conn


def register(mcp: "FastMCP") -> None:

    @mcp.tool()
    def task_create(
        title: str,
        description: str = "",
        priority: str = "normal",
        due_date: str = "",
        tags: list[str] = [],
    ) -> dict:
        """创建新任务。
        priority: low | normal | high
        due_date: ISO 8601 日期，如 2026-05-10，可留空
        """
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO tasks (title, description, priority, due_date, tags) VALUES (?,?,?,?,?)",
                (title, description, priority, due_date or None, json.dumps(tags, ensure_ascii=False)),
            )
            return {"id": cur.lastrowid, "title": title, "status": "todo"}

    @mcp.tool()
    def task_list(
        status: str = "",
        priority: str = "",
        keyword: str = "",
    ) -> list[dict]:
        """查询任务列表。
        status: todo | in_progress | done | cancelled，留空返回所有
        """
        sql = "SELECT * FROM tasks WHERE 1=1"
        params: list = []
        if status:
            sql += " AND status=?"; params.append(status)
        if priority:
            sql += " AND priority=?"; params.append(priority)
        if keyword:
            sql += " AND (title LIKE ? OR description LIKE ?)"
            params += [f"%{keyword}%", f"%{keyword}%"]
        sql += " ORDER BY CASE priority WHEN 'high' THEN 0 WHEN 'normal' THEN 1 ELSE 2 END, created_at DESC"
        with get_conn() as conn:
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

    @mcp.tool()
    def task_update(
        id: int,
        title: str = "",
        description: str = "",
        status: str = "",
        priority: str = "",
        due_date: str = "",
        tags: list[str] = [],
    ) -> dict:
        """更新任务字段，只传需要修改的字段。
        status: todo | in_progress | done | cancelled
        """
        fields, params = [], []
        if title:          fields.append("title=?");       params.append(title)
        if description:    fields.append("description=?"); params.append(description)
        if status:         fields.append("status=?");      params.append(status)
        if priority:       fields.append("priority=?");    params.append(priority)
        if due_date:       fields.append("due_date=?");    params.append(due_date)
        if tags:           fields.append("tags=?");        params.append(json.dumps(tags, ensure_ascii=False))
        if not fields:
            return {"error": "no fields provided"}
        fields.append("updated_at=?")
        params.append(datetime.now().isoformat(timespec="seconds"))
        params.append(id)
        with get_conn() as conn:
            conn.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id=?", params)
            return {"id": id, "updated": True}

    @mcp.tool()
    def task_delete(id: int) -> dict:
        """删除任务。"""
        with get_conn() as conn:
            conn.execute("DELETE FROM tasks WHERE id=?", (id,))
            return {"id": id, "deleted": True}
