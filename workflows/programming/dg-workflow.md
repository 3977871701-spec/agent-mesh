# 编程项目工作流 - 主 Agent 调度手册

## 概述
本工作流用于执行编程任务，由主 Agent 调度各专业子 Agent 协作完成。

## 角色映射

| 子 Agent | 对应 md 配置 |
|----------|--------------|
| dg-planner | `dg-planner.md` |
| dg-dev | `dg-dev.md` |
| dg-frontend-test | `dg-frontend-test.md` |
| dg-backend | `dg-backend.md` |
| dg-port | `dg-port.md` |
| dg-webapp-test | `dg-webapp-test.md` |

## 执行流程

```
┌─────────────────────────────────────────────────────────────┐
│  Phase 1: 计划                                              │
│  ┌─────────────┐                                           │
│  │ dg-planner  │ → dev-plan.md + SPEC.md                  │
│  └─────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 2: 批量开发循环                                       │
│                                                             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐                 │
│  │ dg-dev  │ → │ dg-port │ → │ dg-... │ (根据任务)       │
│  └─────────┘    └─────────┘    └─────────┘                 │
│                          ↓                                  │
│  ┌─────────────────────────────────────────┐               │
│  │ 三维测试（并发）                          │               │
│  │ dg-frontend-test │ dg-frontend-test │ dg-webapp-test │
│  └─────────────────────────────────────────┘               │
│                          ↓                                  │
│  ┌─────────────────────────────────────────┐               │
│  │ 修正循环（最多 3 轮）                      │               │
│  │ 修复 → 测试 → 验收                         │               │
│  └─────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

## 完整执行步骤

### Step 1: 初始化
主 Agent 执行：
```bash
# 确认输出目录
mkdir -p {OUTPUT_DIR}

# 创建日志
touch {OUTPUT_DIR}/main-log.md

# 探测现有 Agent ID
find ~/.claude/projects/ -name "agent-*.meta.json" -type f -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1
```

### Step 2: 启动计划 Agent
```javascript
Agent({
  subagent_type: "dg-planner",
  prompt: `
项目需求：{用户需求描述}
输出目录：{OUTPUT_DIR}

请阅读 dg-planner.md 配置，产出 dev-plan.md 和 SPEC.md。
完成后只返回文件路径列表。
  `
})
```

### Step 3: 批量开发
```javascript
Agent({
  subagent_type: "dg-dev",
  run_in_background: true,
  prompt: `
开发任务：{任务列表}
dev-plan：{OUTPUT_DIR}/dev-plan.md
SPEC：{OUTPUT_DIR}/SPEC.md
lessons-learned：{OUTPUT_DIR}/lessons-learned.md
输出目录：{OUTPUT_DIR}

请阅读 dg-dev.md，按计划开发。
  `
})
```

### Step 4: 后端与端口开发
```javascript
Agent({
  subagent_type: "dg-backend",
  prompt: `
dev-plan：{OUTPUT_DIR}/dev-plan.md
SPEC：{OUTPUT_DIR}/SPEC.md
输出目录：{OUTPUT_DIR}
  `
})

Agent({
  subagent_type: "dg-port",
  prompt: `
API 设计：{OUTPUT_DIR}/api-design.md
后端代码：{后端路径}
前端代码：{前端路径}
输出目录：{OUTPUT_DIR}
  `
})
```

### Step 5: 三维测试
```javascript
// 并发启动 3 个测试 Agent
Agent({
  subagent_type: "dg-frontend-test",
  prompt: `测试类型：frontend`
})

Agent({
  subagent_type: "dg-frontend-test",
  prompt: `测试类型：port`
})

Agent({
  subagent_type: "dg-webapp-test",
  prompt: `测试次数：3`
})
```

### Step 6: 修正循环
如测试 FAIL：
```javascript
Agent({
  subagent_type: "dg-dev",
  prompt: `
修复任务：{测试报告中的问题}
问题代码：{路径}
  `
})
// 修复后重新测试
// 最多循环 3 次
```

### Step 7: 验收
所有测试 PASS 后：
```javascript
Agent({
  subagent_type: "dg-webapp-test",
  prompt: `最终验收测试`
})
```

## 日志格式
写入 `{OUTPUT_DIR}/main-log.md`：
```
# {项目名} - 主日志

## {yymmdd hhmm} 项目启动
需求：{简要描述}

## {yymmdd hhmm} 计划完成
任务数：{N}
dev-plan：{路径}

## {yymmdd hhmm} 开发完成
{DEV_ID：xxx}
完成：{任务列表}

## {yymmdd hhmm} 测试完成
通过项：{N}
问题数：{N}
测试报告：{路径}

## {yymmdd hhmm} 项目完成
```

## 禁止事项
- ❌ 不直接修改代码
- ❌ 不读取报告全文内容
- ❌ 不跳过 ID 提取
- ❌ 不启动新的 DEV_ID 用于修正循环
