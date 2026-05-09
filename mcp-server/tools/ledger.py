"""Ledger tools — personal income/expense tracking."""
from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

from db import get_conn


def register(mcp: "FastMCP") -> None:

    @mcp.tool()
    def ledger_add(
        amount: float,
        type: str = "expense",
        category: str = "",
        note: str = "",
        date: str = "",
        tags: list[str] = [],
    ) -> dict:
        """记录一笔收支。
        amount: 金额（正数）
        type: 'expense'（支出）或 'income'（收入）
        category: 分类，如 餐饮/交通/购物/医疗/娱乐/工资/其他
        note: 备注说明
        date: 日期 YYYY-MM-DD，默认今天
        """
        if amount <= 0:
            return {"error": "amount must be positive"}
        if type not in ("expense", "income"):
            return {"error": "type must be 'expense' or 'income'"}
        entry_date = date or datetime.now().strftime("%Y-%m-%d")
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO transactions (amount, type, category, note, date, tags) VALUES (?,?,?,?,?,?)",
                (amount, type, category, note, entry_date, json.dumps(tags, ensure_ascii=False)),
            )
            return {"id": cur.lastrowid, "amount": amount, "type": type, "category": category, "date": entry_date}

    @mcp.tool()
    def ledger_list(
        start_date: str = "",
        end_date: str = "",
        type: str = "",
        category: str = "",
        limit: int = 30,
    ) -> list[dict]:
        """查询账单流水。
        start_date / end_date: YYYY-MM-DD，不填则不限制
        type: 'expense' 或 'income'，不填则全部
        category: 按分类筛选，不填则全部
        """
        where, params = [], []
        if start_date:
            where.append("date >= ?"); params.append(start_date)
        if end_date:
            where.append("date <= ?"); params.append(end_date)
        if type:
            where.append("type = ?"); params.append(type)
        if category:
            where.append("category = ?"); params.append(category)
        clause = ("WHERE " + " AND ".join(where)) if where else ""
        params.append(limit)
        with get_conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM transactions {clause} ORDER BY date DESC, id DESC LIMIT ?",
                params,
            ).fetchall()
            return [dict(r) for r in rows]

    @mcp.tool()
    def ledger_summary(
        start_date: str = "",
        end_date: str = "",
    ) -> dict:
        """按分类汇总收支，返回总收入、总支出、结余及各分类明细。
        start_date / end_date: YYYY-MM-DD，不填则统计全部数据
        """
        where, params = [], []
        if start_date:
            where.append("date >= ?"); params.append(start_date)
        if end_date:
            where.append("date <= ?"); params.append(end_date)
        clause = ("WHERE " + " AND ".join(where)) if where else ""

        with get_conn() as conn:
            # Totals
            totals = conn.execute(
                f"""SELECT type, SUM(amount) as total
                    FROM transactions {clause}
                    GROUP BY type""",
                params,
            ).fetchall()
            income = next((r["total"] for r in totals if r["type"] == "income"), 0.0)
            expense = next((r["total"] for r in totals if r["type"] == "expense"), 0.0)

            # By category
            by_cat = conn.execute(
                f"""SELECT type, category, SUM(amount) as total, COUNT(*) as count
                    FROM transactions {clause}
                    GROUP BY type, category
                    ORDER BY type, total DESC""",
                params,
            ).fetchall()

        return {
            "income": round(income, 2),
            "expense": round(expense, 2),
            "balance": round(income - expense, 2),
            "by_category": [dict(r) for r in by_cat],
        }

    @mcp.tool()
    def ledger_delete(id: int) -> dict:
        """删除一条账单记录。"""
        with get_conn() as conn:
            conn.execute("DELETE FROM transactions WHERE id=?", (id,))
            return {"id": id, "deleted": True}
