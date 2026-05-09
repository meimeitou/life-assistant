---
name: calendar
description: 管理日历事件，记录和查询有明确时间的日程安排
---

# Calendar Skill

## 什么时候用 Calendar

有**明确开始时间**的事情用 Calendar：

- ✅ 约会、会议、复查、课程、演出
- ✅ 航班、火车（有出发时间）
- ❌ 需要在某天完成但时间灵活 → Todo
- ❌ 只需要到时间收到提醒 → Reminder

## 时间解析

| 用户说               | 解析结果                    |
| -------------------- | --------------------------- |
| "今天下午两点"       | today 14:00                 |
| "明天早上 10 点"     | tomorrow 10:00              |
| "下周三下午两点"     | next Wednesday 14:00        |
| "5 月 20 号晚上八点" | 05-20 20:00（当年或下一年） |
| 未说结束时间         | 默认 duration = 1 小时      |

## 工具

`event_create` / `event_list` / `event_update` / `event_delete`（均由 `life-mcp` 提供）

**event_create 关键字段**：`title`（必填）、`start_time`（ISO 8601）、`end_time`、`location`、`description`

## 示例

**新建**

- "下周三下午两点有个牙科复查，地点 XX 口腔" → event_create(title="牙科复查", start_time="2026-05-13T14:00", location="XX 口腔")
- "明天早上 9 点到 11 点有个组会" → event_create(title="组会", start_time="...T09:00", end_time="...T11:00")
- "6 月 18 号买了演唱会票，晚上 7 点半" → event_create(title="演唱会", start_time="2026-06-18T19:30")

**查询**

- "我这周有什么安排" → event_list(start=本周一, end=本周日)
- "明天有事吗" → event_list(start=tomorrow, end=tomorrow)

**更新 / 删除**

- "把周三的复查改到周四下午三点" → event_update(id=?, start_time=新时间)
- "取消明天的会议" → event_delete(id=?)
