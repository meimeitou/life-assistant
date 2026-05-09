---
name: ledger
description: 记录日常收支，查询账单流水，按分类汇总统计
---

# Ledger Skill

## 记账

当用户说"记账"、"花了"、"收到"、"买了"等，立刻调用 `ledger_add`，不需要询问确认。

**分类参考**（category 字段）：
餐饮、交通、购物、医疗、娱乐、住房、工资、转账、其他

**提取规则**：

- "花了 38 块吃饭" → amount=38, type=expense, category=餐饮
- "打车花了 23.5" → amount=23.5, type=expense, category=交通
- "收到工资 15000" → amount=15000, type=income, category=工资
- "今天买咖啡 28" → amount=28, type=expense, category=餐饮, date=今天

日期默认今天，如用户提及"昨天"、"上周五"等需转换为 YYYY-MM-DD 格式。

## 查询账单

- "这个月花了多少" → `ledger_summary(start_date="YYYY-MM-01", end_date="今天")`
- "看看最近的账单" → `ledger_list(limit=20)`
- "这个月餐饮花了多少" → `ledger_list(start_date=..., category="餐饮")` 后求和，或 `ledger_summary` 后取分类
- "今年收入总计" → `ledger_summary(start_date="YYYY-01-01")`

## 工具

| 工具             | 用途                                           |
| ---------------- | ---------------------------------------------- |
| `ledger_add`     | 记录一笔收支（amount 必填，type 默认 expense） |
| `ledger_list`    | 查询流水，支持日期/类型/分类筛选               |
| `ledger_summary` | 按分类汇总，返回总收入/总支出/结余             |
| `ledger_delete`  | 删除一条记录                                   |
