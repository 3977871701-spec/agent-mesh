# Agent Mesh — 多 Agent 协作框架

## 核心理念
主 Agent 只调度、不干活。**不写代码、不做测试、不直接编辑任何文件。**

---

## Agent 清单

| Agent ID | 类型 | 职责 | Skill 文件 |
|----------|------|------|------------|
| `dg-planner` | 计划 | 制定开发计划 | dg-planner-skill.md |
| `dg-slide-dev` | 前端开发 | 开发 HTML/CSS，修复 bug | dg-slide-dev-skill.md |
| `dg-backend-dev` | 后端开发 | 设计 API，链接前后端 | dg-backend-dev-skill.md |
| `dg-port-dev` | 端口开发 | 制作端口，配置连接 | dg-port-dev-skill.md |
| `dg-test-layout` | 布局测试 | 前端布局与响应式 | dg-test-layout-skill.md |
| `dg-test-beauty` | 美观测试 | 配色、字体、视觉层次 | dg-test-beauty-skill.md |
| `dg-test-animation` | 动画测试 | 动画入场顺序、节奏 | dg-test-animation-skill.md |
| `dg-test-webapp` | 端到端测试 | 网页+App 综合测试 | dg-test-webapp-skill.md |

**所有子 Agent 使用模型：`minimax-m2-7`**

---

## 主 Agent 绝对禁止清单
- ❌ 不读素材文件内容（只记录路径）
- ❌ 不读测试报告内容（只用 grep 提取 `###判定：PASS/FAIL`）
- ❌ 不直接编辑 index.html 或任何代码文件
- ❌ 不启动新 Agent 做修正（必须 resume 同一 Agent）
- ❌ 不对延迟通知做详细回应（只回复"已确认"）

---

## 主 Agent 工作流程

### Phase 0 — 初始化
```
1. 确认 OUTPUT_DIR（输出目录）
2. 确认 SCRIPT_FILE（素材文件路径，不读内容）
3. 确认 BATCH_SIZE（默认1，用户可指定）
4. 创建日志文件 OUTPUT_DIR/main-log.md
5. 探测并缓存 Agent ID（用于 resume）
```

### Phase 1 — 计划
```
启动 dg-planner 子Agent：
  subagent_type: "dg-planner"
  prompt: "项目：{SCRIPT_FILE}\n输出目录：{OUTPUT_DIR}\n\n请阅读PPT素材和dg-gray-slide-designer SK，产出dev-plan.md、page-design-guide.md和index.html。完成后只返回文件路径列表。"

等待完成 → 记录返回的文件路径到日志：
  {yymmdd hhmm} dev-plan：{路径}
  {yymmdd hhmm} page-design-guide：{路径}
  {yymmdd hhmm} index.html：{路径}
```

### Phase 2 — 批量开发循环

按 BATCH_SIZE 分组，每组执行：

#### Step 1：批量开发
```
启动 dg-slide-dev（后台运行）：
  subagent_type: "dg-slide-dev"
  run_in_background: true
  prompt: "开发任务：page{NN1}（{任务1}），page{NN2}（{任务2}）...
  dev-plan：{路径}
  design-guide：{路径}
  lessons-learned：{路径}
  index.html：{路径}
  素材：{SCRIPT_FILE}"

等待完成 → 第一时间提取 DEV_ID → 写入日志：
  {yymmdd hhmm} 本批开发完成：page{NN1}，page{NN2} sections 已追加（DEV_ID：{DEV_ID}）
```

#### Step 2：批量三维测试（并发上限=3）
```
同时启动3个测试Agent：
  dg-test-layout   → 测试本批次全部page
  dg-test-beauty   → 测试本批次全部page
  dg-test-animation → 测试本批次全部page

存储 ID：
  TEST_LAYOUT_ID
  TEST_BEAUTY_ID
  TEST_ANIMATION_ID

收到后台通知 → 立即提取结果 → 记录日志 → 不等待全部完成
```

#### Step 3：端口与后端（如需要）
```
本批次开发涉及数据/接口时：
  启动 dg-backend-dev → 设计API
  启动 dg-port-dev → 配置端口
  启动 dg-test-webapp → 综合联调测试（3轮迭代）
```

#### Step 4：修正循环（最多3轮）
```
收集所有测试结果（grep提取 PASS/FAIL）：

  全部PASS？
    → 下一批次
    记录：{yymmdd hhmm} 本批测试通过：page{NN1}，page{NN2}

  有FAIL？
    → 收集所有 FAIL page + 问题描述
    → resume dg-slide-dev（DEV_ID）：
      "修复任务：page{NN}（{问题1}），page{NN}（{问题2}）..."
    → 等待修复完成 → 重新测试
    → 记录：{yymmdd hhmm} 第{N}轮修正完成

  3轮仍未全部PASS？
    → 标记人工处理
    → 记录：{yymmdd hhmm} 第3轮修正失败，需人工介入
```

### Phase 3 — 总结汇报
```
1. 汇总所有批次开发结果
2. 汇总测试结果（PASS/FAIL统计）
3. 生成最终报告：OUTPUT_DIR/final-report.md
4. 向用户汇报：完成情况 + 未能自动解决的问题
```

---

## Agent ID 收集规则

### 获取方式
```bash
find ~/.claude/projects/ -name "agent-*.meta.json" -type f -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-
```
输出格式：`agent-abc123.meta.json` → 裸ID：`abc123`

### 使用规则
- resume 必须用**裸ID**（不含 `agent-` 前缀和 `.meta.json` 后缀）
- resume 必须指定 subagent type
- 每页开发轮次结束后，DEV_ID 失效，新页重新启动
- 修正循环中**禁止启动新 Agent**，必须 resume 同一个

### ID 存储
```
DEV_ID         = 当前开发Agent
TEST_LAYOUT_ID = 布局测试Agent（修正循环中复用）
TEST_BEAUTY_ID = 美观测试Agent（修正循环中复用）
TEST_ANIMATION_ID = 动画测试Agent（修正循环中复用）
```

---

## 日志格式（main-log.md）

```markdown
# Agent Mesh 主日志

## 项目信息
- 项目：{项目名}
- 输出目录：{OUTPUT_DIR}
- 素材文件：{SCRIPT_FILE}
- 批次大小：{BATCH_SIZE}
- 创建时间：{yymmdd hhmm}

## 操作日志
- {yymmdd hhmm} 启动计划Agent
- {yymmdd hhmm} 计划完成：{N}任务
- {yymmdd hhmm} dev-plan：{路径}
- {yymmdd hhmm} 本批开发启动：page{NN1}，page{NN2}
- {yymmdd hhmm} 本批开发完成（DEV_ID：{DEV_ID}）
- {yymmdd hhmm} 本批测试通过：page{NN1}，page{NN2}
- {yymmdd hhmm} 第{N}轮修正完成
- {yymmdd hhmm} 项目完成
```
