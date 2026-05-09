"""Calendar event CRUD tools."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

from db import get_conn


def register(mcp: "FastMCP") -> None:

    @mcp.tool()
    def event_create(
        title: str,
        start_time: str,
        end_time: str = "",
        location: str = "",
        description: str = "",
        recurrence: str = "",
    ) -> dict:
        """创建日历事件。
        start_time / end_time: ISO 8601，如 2026-05-10T14:00:00
        recurrence: 重复规则，如 "每周一" 或 RRULE 字符串，可留空
        """
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO events (title, start_time, end_time, location, description, recurrence) VALUES (?,?,?,?,?,?)",
                (title, start_time, end_time or None, location, description, recurrence),
            )
            return {"id": cur.lastrowid, "title": title, "start_time": start_time}

    @mcp.tool()
    def event_list(start: str = "", end: str = "") -> list[dict]:
        """查询日历事件。
        start / end: ISO 8601 日期，如 2026-05-01，留空不过滤
        """
        sql = "SELECT * FROM events WHERE 1=1"
        params: list = []
        if start:
            sql += " AND start_time >= ?"; params.append(start)
        if end:
            sql += " AND start_time <= ?"; params.append(end)
        sql += " ORDER BY start_time ASC"
        with get_conn() as conn:
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

    @mcp.tool()
    def event_update(
        id: int,
        title: str = "",
        start_time: str = "",
        end_time: str = "",
        location: str = "",
        description: str = "",
        recurrence: str = "",
    ) -> dict:
        """更新日历事件字段，只传需要修改的字段。"""
        fields, params = [], []
        if title:       fields.append("title=?");       params.append(title)
        if start_time:  fields.append("start_time=?");  params.append(start_time)
        if end_time:    fields.append("end_time=?");    params.append(end_time)
        if location:    fields.append("location=?");    params.append(location)
        if description: fields.append("description=?"); params.append(description)
        if recurrence:  fields.append("recurrence=?");  params.append(recurrence)
        if not fields:
            return {"error": "no fields provided"}
        fields.append("updated_at=?")
        params.append(datetime.now().isoformat(timespec="seconds"))
        params.append(id)
        with get_conn() as conn:
            conn.execute(f"UPDATE events SET {', '.join(fields)} WHERE id=?", params)
            return {"id": id, "updated": True}

    @mcp.tool()
    def event_delete(id: int) -> dict:
        """删除日历事件。"""
        with get_conn() as conn:
            conn.execute("DELETE FROM events WHERE id=?", (id,))
            return {"id": id, "deleted": True}
