"""Habit tracking tools — define habits, log daily check-ins, query stats."""
from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

from db import get_conn


def register(mcp: "FastMCP") -> None:

    @mcp.tool()
    def habit_create(
        name: str,
        target_value: float = None,
        unit: str = "",
        frequency: str = "daily",
    ) -> dict:
        """创建一个习惯目标。
        name: 习惯名称，如"看书"、"运动"
        target_value: 每次目标量，如 30（可选）
        unit: 单位，如 min / km / 次（可选）
        frequency: daily（每天）或 weekly（每周），默认 daily
        """
        if not name:
            return {"error": "name is required"}
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO habits (name, target_value, unit, frequency) VALUES (?,?,?,?)",
                (name, target_value, unit, frequency),
            )
            return {"id": cur.lastrowid, "name": name, "target_value": target_value, "unit": unit, "frequency": frequency}

    @mcp.tool()
    def habit_list(active_only: bool = True) -> list[dict]:
        """列出所有习惯目标。
        active_only: True 只返回进行中的习惯，False 返回全部（含已归档）
        """
        with get_conn() as conn:
            if active_only:
                rows = conn.execute("SELECT * FROM habits WHERE active = 1 ORDER BY id").fetchall()
            else:
                rows = conn.execute("SELECT * FROM habits ORDER BY id").fetchall()
            return [dict(r) for r in rows]

    @mcp.tool()
    def habit_update(
        id: int,
        name: str = "",
        target_value: float = None,
        unit: str = "",
        active: bool = None,
    ) -> dict:
        """修改习惯目标，或将其归档（active=false）。"""
        fields, params = [], []
        if name:
            fields.append("name = ?"); params.append(name)
        if target_value is not None:
            fields.append("target_value = ?"); params.append(target_value)
        if unit:
            fields.append("unit = ?"); params.append(unit)
        if active is not None:
            fields.append("active = ?"); params.append(1 if active else 0)
        if not fields:
            return {"error": "nothing to update"}
        params.append(id)
        with get_conn() as conn:
            conn.execute(f"UPDATE habits SET {', '.join(fields)} WHERE id = ?", params)
            row = conn.execute("SELECT * FROM habits WHERE id = ?", (id,)).fetchone()
            return dict(row) if row else {"error": "not found"}

    @mcp.tool()
    def habit_checkin(
        habit_id: int,
        value: float = None,
        date: str = "",
        notes: str = "",
    ) -> dict:
        """记录习惯打卡（每天一次，重复打卡会覆盖当天记录）。
        habit_id: 习惯 ID（可先用 habit_list 查询）
        value: 实际完成量，如看书 25 分钟填 25（可选）
        date: 打卡日期 YYYY-MM-DD，默认今天
        notes: 备注（可选）
        """
        checkin_date = date or _today()
        with get_conn() as conn:
            habit = conn.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)).fetchone()
            if not habit:
                return {"error": f"habit {habit_id} not found"}
            conn.execute(
                """INSERT INTO habit_logs (habit_id, date, value, notes)
                   VALUES (?,?,?,?)
                   ON CONFLICT(habit_id, date) DO UPDATE SET
                       value = excluded.value,
                       notes = excluded.notes""",
                (habit_id, checkin_date, value, notes),
            )
            return {
                "habit_id": habit_id,
                "habit_name": habit["name"],
                "date": checkin_date,
                "value": value,
                "target": habit["target_value"],
                "unit": habit["unit"],
            }

    @mcp.tool()
    def habit_stats(
        habit_id: int,
        start_date: str = "",
        end_date: str = "",
    ) -> dict:
        """查询习惯的完成情况统计（完成率、连续天数、明细）。
        habit_id: 习惯 ID
        start_date / end_date: YYYY-MM-DD，默认最近 30 天
        """
        end = end_date or _today()
        start = start_date or _date_offset(end, -29)
        with get_conn() as conn:
            habit = conn.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)).fetchone()
            if not habit:
                return {"error": f"habit {habit_id} not found"}
            logs = conn.execute(
                "SELECT * FROM habit_logs WHERE habit_id = ? AND date BETWEEN ? AND ? ORDER BY date DESC",
                (habit_id, start, end),
            ).fetchall()

        total_days = (
            _parse_date(end) - _parse_date(start)
        ).days + 1
        completed_days = len(logs)
        completion_rate = round(completed_days / total_days * 100, 1) if total_days > 0 else 0

        # Calculate current streak (consecutive days ending today or yesterday)
        streak = _calc_streak(habit_id, end)

        return {
            "habit": dict(habit),
            "period": {"start": start, "end": end, "total_days": total_days},
            "completed_days": completed_days,
            "completion_rate": f"{completion_rate}%",
            "current_streak": streak,
            "logs": [dict(r) for r in logs],
        }

    @mcp.tool()
    def habit_log_delete(id: int) -> dict:
        """删除一条打卡记录（误打时使用）。"""
        with get_conn() as conn:
            conn.execute("DELETE FROM habit_logs WHERE id = ?", (id,))
            return {"id": id, "deleted": True}


def _today() -> str:
    return date.today().isoformat()


def _parse_date(s: str) -> date:
    return date.fromisoformat(s)


def _date_offset(base: str, days: int) -> str:
    return (_parse_date(base) + timedelta(days=days)).isoformat()


def _calc_streak(habit_id: int, up_to: str) -> int:
    """Count consecutive logged days ending on or before up_to."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT date FROM habit_logs WHERE habit_id = ? AND date <= ? ORDER BY date DESC",
            (habit_id, up_to),
        ).fetchall()
    if not rows:
        return 0
    dates = {_parse_date(r["date"]) for r in rows}
    cursor = _parse_date(up_to)
    # Allow streak to start from today or yesterday
    if cursor not in dates:
        cursor = cursor - timedelta(days=1)
    streak = 0
    while cursor in dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak
