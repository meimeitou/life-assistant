---
name: todo
description: 管理待办任务，支持优先级、截止日和状态跟踪
---

# Todo Skill

## 什么时候用 Todo

Todo 适合**有行动项、需要跟进**的事情：

- ✅ 需要在某个时间点之前完成 → Todo（可加截止日）
- ✅ 需要记住「做某事」而不只是「知道某事」→ Todo
- ❌ 只是记录信息、想法 → Notes
- ❌ 有明确的开始时间（约会/会议）→ Calendar
- ❌ 需要到时间自动推送提醒 → Reminder

## 优先级识别

| 用户说                         | priority |
| ------------------------------ | -------- |
| 「很急」「必须」「今天必须做」 | `high`   |
| 普通描述，无特殊强调           | `normal` |
| 「有空再说」「不急」           | `low`    |

## 状态流转

`todo` → `in_progress` → `done` | `cancelled`

## 工具

`task_create` / `task_list` / `task_update` / `task_delete`（均由 `life-mcp` 提供）

## 示例

**新建**

- "记一下，要去办居住证" → task_create(title="办居住证")
- "帮我记个任务，下周五之前把报告发给老板，很紧" → task_create(title="发报告给老板", priority="high", due="下周五")
- "有空去配个眼镜" → task_create(title="配眼镜", priority="low")

**查询**

- "我现在有哪些待办" → task_list(status="todo")
- "有什么高优先级没做的" → task_list(priority="high", status="todo")

**更新**

- "居住证办好了" → task_update(id=?, status="done")
- "把买书包改成高优先级，截止日下周五" → task_update(id=?, priority="high", due="下周五")
- "先把这个任务搁置" → task_update(id=?, status="cancelled")
