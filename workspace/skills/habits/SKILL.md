---
name: habits
description: 习惯培养与打卡追踪，记录每天完成情况，统计完成率和连续天数
---

# Habits Skill

## 什么时候用 Habits

用于**持续性目标追踪**，需要每天/每周重复完成并记录进度：

- ✅ 每天看书 30 分钟
- ✅ 每天运动 45 分钟
- ✅ 每天冥想 10 分钟
- ✅ 每周跑步 3 次
- ❌ 单次运动记录（跑了 5 公里）→ Health（health_log_add）
- ❌ 一次性任务（买书）→ Todo

## 工具

| 工具               | 用途                 |
| ------------------ | -------------------- |
| `habit_create`     | 新建习惯目标         |
| `habit_list`       | 查看所有习惯         |
| `habit_update`     | 修改目标 / 归档习惯  |
| `habit_checkin`    | 今日打卡             |
| `habit_stats`      | 查看完成率、连续天数 |
| `habit_log_delete` | 删除误打记录         |

## 典型对话

### 创建习惯

- "我想每天看书 30 分钟" → habit_create(name="看书", target_value=30, unit="min")
- "我要每天运动" → habit_create(name="运动", target_value=45, unit="min")
- "每天冥想" → habit_create(name="冥想")
- "每周跑步 3 次" → habit_create(name="跑步", target_value=3, unit="次", frequency="weekly")

### 打卡

- "今天看书了" → 先 habit_list 找到"看书"的 id，再 habit_checkin(habit_id=?)（value 留空，用户未说时长）
- "今天看书了 45 分钟" → habit_checkin(habit_id=?, value=45)
- "昨天忘记打卡了" → habit_checkin(habit_id=?, date="2026-05-08")
- "今天运动、看书都完成了" → 分别 checkin 两个习惯

### 查看进度

- "我最近看书完成率怎么样" → habit_stats(habit_id=?)，返回 completion_rate 和 current_streak
- "这个月的运动习惯情况" → habit_stats(habit_id=?, start_date="2026-05-01", end_date="2026-05-31")
- "我现在有哪些习惯在追踪" → habit_list()

### 修改 / 归档

- "把看书目标改成 60 分钟" → habit_update(id=?, target_value=60)
- "我不想追踪运动了" → habit_update(id=?, active=false)

## 字段说明

**habit_create**：

- `name`：必填
- `target_value`：目标量，如 30（可选，只打卡不计量时可不填）
- `unit`：单位，如 `min` / `km` / `次`（可选）
- `frequency`：`daily`（每天，默认）或 `weekly`（每周）

**habit_checkin**：

- `habit_id`：必填，从 habit_list 获取
- `value`：实际完成量（可选）
- `date`：默认今天，YYYY-MM-DD
- 同一天重复打卡会覆盖当天记录

**habit_stats 返回**：

- `completion_rate`：区间内完成率，如 `"80%"`
- `current_streak`：当前连续打卡天数
- `completed_days`：区间内完成天数
- `logs`：打卡明细列表
