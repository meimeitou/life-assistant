---
name: health
description: 记录和分析健康数据，包括经期、睡眠、运动、体重等身体指标
---

# Health Skill

## 什么时候用 Health

身体状态的**时序记录**，后续需要统计分析的用 Health：

- ✅ 经期开始/结束
- ✅ 睡眠时间（几点睡、几点起）
- ✅ 运动记录（类型、时长、距离）
- ✅ 体重、体温等数值指标
- ✅ 如厕记录
- ❌ 医院就诊预约（有明确时间的日程）→ Calendar
- ❌ "买体重秤"这类行动项 → Todo

## 类型约定（type 字段）

| 场景     | type          | value 含义       | unit |
| -------- | ------------- | ---------------- | ---- |
| 经期     | `menstrual`   | —                | —    |
| 睡眠     | `sleep`       | 睡眠时长（可选） | min  |
| 跑步     | `exercise`    | 距离             | km   |
| 其他运动 | `exercise`    | 时长             | min  |
| 体重     | `weight`      | 体重             | kg   |
| 体温     | `temperature` | 体温             | ℃    |
| 如厕     | `bowel`       | —                | —    |
| 心情     | `mood`        | 评分 1-10        | —    |

type 字段开放，用户可以用任意字符串。

## 工具

`health_log_add` / `health_log_list` / `health_log_update` / `health_log_delete`

**health_log_add 关键字段**：`type`（必填）、`start_time`（必填，ISO 8601）、`subject`（默认 `"self"`）、`end_time`、`value`、`unit`、`notes`

**subject 约定**：不指定记录对象时默认 `"self"`（自己）。记他人时填姓名，如 `"妈妈"`、`"小明"`。`health_log_list` 也支持按 `subject` 筛选。

## 示例

### 经期

- "今天来月经了" → health_log_add(type="menstrual", start_time="2026-05-09")
- "5 月 6 号来月经的" → health_log_add(type="menstrual", start_time="2026-05-06")
- "今天月经结束了" → 查最近 menstrual 记录的 id，health_log_update(id=?, end_time="2026-05-09")
- "今天来月经了，有点痛" → health_log_add(type="menstrual", start_time="2026-05-09", notes="痛经")
- "帮我记一下我妈今天来月经了" → health_log_add(type="menstrual", start_time="2026-05-09", subject="妈妈")

### 睡眠

- "昨晚 11 点睡，今早 7 点起" → health_log_add(type="sleep", start_time="2026-05-08T23:00", end_time="2026-05-09T07:00")
- "记录一下今天睡了 8 小时" → health_log_add(type="sleep", start_time="2026-05-09", value=480, unit="min")

### 运动

- "刚跑了 5 公里" → health_log_add(type="exercise", start_time="2026-05-09T14:30", value=5, unit="km", notes="跑步")
- "健身 1 小时" → health_log_add(type="exercise", start_time="2026-05-09T14:30", value=60, unit="min", notes="健身")

### 体重

- "今天体重 55.2 公斤" → health_log_add(type="weight", start_time="2026-05-09", value=55.2, unit="kg")

## 查询与分析

**查历史**

- "我上次月经是几号" → health_log_list(type="menstrual", subject="self", limit=1)
- "妈妈上次月经是几号" → health_log_list(type="menstrual", subject="妈妈", limit=1)
- "这个月的睡眠记录" → health_log_list(type="sleep", start_date="2026-05-01", end_date="2026-05-31")
- "小明最近的体重记录" → health_log_list(type="weight", subject="小明")

**分析规律**（拿到列表后由 LLM 计算）

- "最近几个月月经规律吗" → health_log_list(type="menstrual", limit=12)，按 start_time 排序，计算相邻间隔天数，正常范围 21～35 天
- "我平均经期几天" → 用 end_time - start_time 求均值（仅含 end_time 的记录）
- "我最近平均睡几个小时" → health_log_list(type="sleep")，计算 end_time - start_time 或 value 均值
- "这个月体重趋势" → health_log_list(type="weight", start_date=...) 按时间排列 value
