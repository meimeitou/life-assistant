"""Health log tools — tracking menstrual cycles, sleep, exercise, and other body metrics."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

from db import get_conn

# Known types for reference (open-ended — user can add any type)
# menstrual / sleep / exercise / bowel / weight / mood / ...


def register(mcp: "FastMCP") -> None:

    @mcp.tool()
    def health_log_add(
        type: str,
        start_time: str,
        subject: str = "self",
        end_time: str = "",
        value: float = None,
        unit: str = "",
        notes: str = "",
    ) -> dict:
        """记录一条健康日志（经期、睡眠、运动、如厕等）。
        type: 记录类型，如 menstrual / sleep / exercise / bowel / weight / mood
        start_time: 开始时间，ISO 8601（如 2026-05-09 或 2026-05-09T22:00）
        subject: 记录对象，默认 'self'（自己），记他人时填姓名，如 '妈妈' / '小明'
        end_time: 结束时间（可选）
        value: 数值，如运动距离、体重、睡眠评分（可选）
        unit: 单位，如 km / kg / min（可选）
        notes: 备注，如症状描述
        """
        if not type or not start_time:
            return {"error": "type and start_time are required"}
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO health_logs (type, start_time, subject, end_time, value, unit, notes) VALUES (?,?,?,?,?,?,?)",
                (type, start_time, subject, end_time or None, value, unit, notes),
            )
            return {"id": cur.lastrowid, "type": type, "subject": subject, "start_time": start_time}

    @mcp.tool()
    def health_log_list(
        type: str = "",
        subject: str = "",
        start_date: str = "",
        end_date: str = "",
        limit: int = 50,
    ) -> list[dict]:
        """查询健康日志。
        type: 按类型筛选，不填则返回所有类型
        subject: 按记录对象筛选，不填则返回所有人
        start_date / end_date: YYYY-MM-DD，不填则不限制
        limit: 最多返回条数，默认 50
        """
        where, params = [], []
        if type:
            where.append("type = ?"); params.append(type)
        if subject:
            where.append("subject = ?"); params.append(subject)
        if start_date:
            where.append("start_time >= ?"); params.append(start_date)
        if end_date:
            where.append("start_time <= ?"); params.append(end_date + "T23:59:59")
        clause = ("WHERE " + " AND ".join(where)) if where else ""
        params.append(limit)
        with get_conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM health_logs {clause} ORDER BY start_time DESC LIMIT ?",
                params,
            ).fetchall()
            return [dict(r) for r in rows]

    @mcp.tool()
    def health_log_update(
        id: int,
        end_time: str = "",
        value: float = None,
        unit: str = "",
        notes: str = "",
    ) -> dict:
        """更新一条健康日志（常用于补填结束时间或备注）。
        id: 记录 ID
        """
        fields, params = [], []
        if end_time:
            fields.append("end_time = ?"); params.append(end_time)
        if value is not None:
            fields.append("value = ?"); params.append(value)
        if unit:
            fields.append("unit = ?"); params.append(unit)
        if notes:
            fields.append("notes = ?"); params.append(notes)
        if not fields:
            return {"error": "nothing to update"}
        params.append(id)
        with get_conn() as conn:
            conn.execute(f"UPDATE health_logs SET {', '.join(fields)} WHERE id = ?", params)
            row = conn.execute("SELECT * FROM health_logs WHERE id = ?", (id,)).fetchone()
            return dict(row) if row else {"error": "not found"}

    @mcp.tool()
    def health_log_delete(id: int) -> dict:
        """删除一条健康日志。"""
        with get_conn() as conn:
            conn.execute("DELETE FROM health_logs WHERE id = ?", (id,))
            return {"id": id, "deleted": True}
