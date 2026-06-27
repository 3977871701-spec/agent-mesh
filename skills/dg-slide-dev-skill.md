# dg-slide-dev-skill — 前端开发 Agent

## 职责
根据开发计划和设计指南，开发和修复 HTML/CSS 页面程序。**不直接修改 index.html 以外的任何代码文件**。每完成一个 page 立即追加到 index.html。

## 输入
- `dev-plan.md` 路径 — 任务列表
- `page-design-guide.md` 路径 — 设计规范
- `lessons-learned.md` 路径 — 经验沉淀（首次可能不存在）
- `index.html` 路径 — 当前进度文件
- `SCRIPT_FILE` 路径 — 口播稿/素材文件路径
- 本次开发任务：page 编号列表

## 必读文件（按顺序）

### 1. index.html 中目标 section
用 `grep` 找到 `<section id="page{NN}"` 的行号，用 `Read` 读取该 section 完整代码。

### 2. page-design-guide.md 中当前页面
理解设计意图：主题、动画入场顺序、间距基准值、特殊要求。

### 3. lessons-learned.md（如存在）
避免重复历史错误。

## 动画规范（来自设计标准）

### 入场顺序（必须严格遵守）
1. 标题（Title）
2. 主角元素（Main Content）
3. 配角元素（Supporting Content）
4. 装饰元素（Decoration）

### 间距基准值
- 元素间 delay 间隔：需 >= 基准值（查 page-design-guide）
- 典型基准值：200ms / 300ms / 500ms（按页面复杂度调整）

### 方向语义
- 标题：通常从上往下（top）
- 主角：从左或右（left/right）
- 装饰：从小到大（scale）

## 判定标准

### PASS
- 零问题或仅有轻微建议
- 所有动画 delay 间隔 >= 基准值
- 入场顺序符合：标题→主角→配角→装饰

### FAIL
- 间距不足（delay < 基准值）
- 顺序混乱（主角先于标题）
- 方向错误（与内容语义不匹配）

## 输出
每次开发完成：
1. 更新 `index.html`，追加本批次所有 page 的 section
2. 如有修复，在同 section 内修改而非新增
3. 写入 `lessons-learned.md`（如有新经验）

## 返回格式
```
开发完成：page{NN1}, page{NN2}, ... sections 已追加
DEV_ID: {agent-id}
```

## 约束
- 主 Agent **绝不直接修改** HTML/CSS 文件
- 所有修复必须通过本 Agent 完成
- 每 page 开发完成后**立即追加**到 index.html，不等本批次全部完成
- 读取 lessons-learned.md，避免重复历史错误
