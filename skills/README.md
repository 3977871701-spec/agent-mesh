# Skills 目录

每个子 Agent 对应一个 `.md` Skill 文件。启动 Agent 时需让其**读取对应的 skill 文件**。

## 文件索引

| Skill 文件 | 对应 Agent | 职责 |
|-----------|-----------|------|
| `dg-planner-skill.md` | dg-planner | 制定开发计划 |
| `dg-slide-dev-skill.md` | dg-slide-dev | 前端 HTML/CSS 开发 |
| `dg-backend-dev-skill.md` | dg-backend-dev | 后端 API 设计 |
| `dg-port-dev-skill.md` | dg-port-dev | 端口服务开发 |
| `dg-test-layout-skill.md` | dg-test-layout | 布局测试 |
| `dg-test-beauty-skill.md` | dg-test-beauty | 美观测试 |
| `dg-test-animation-skill.md` | dg-test-animation | 动画测试 |
| `dg-test-webapp-skill.md` | dg-test-webapp | 端到端综合测试 |
| `WORKFLOW.md` | 主 Agent | 工作流程规范 |

## Agent 启动模板

```json
{
  "subagent_type": "dg-planner",
  "prompt": "请阅读 {OUTPUT_DIR}/skills/dg-planner-skill.md 并按其规范执行。"
}
```

## 快速启动命令
```bash
# 启动计划 Agent
agent --type dg-planner --skill skills/dg-planner-skill.md

# 启动开发 Agent
agent --type dg-slide-dev --skill skills/dg-slide-dev-skill.md

# 启动测试 Agent
agent --type dg-test-animation --skill skills/dg-test-animation-skill.md
```

> 注意：实际启动时请将完整 prompt（包含技能文件路径、项目信息）传给子 Agent。
