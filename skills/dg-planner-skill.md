# dg-planner-skill — 计划 Agent

## 职责
制定项目开发计划，阅读素材文件和设计规范，产出 `dev-plan.md`、`page-design-guide.md` 和初始 `index.html`。

## 输入
- 项目素材文件路径（`口播稿/PPT素材.md`）
- 设计规范文件路径（如 `dg-gray-slide-design-skill.md`）
- 输出目录路径 `OUTPUT_DIR`

## 输出文件

### 1. dev-plan.md
```markdown
# 开发计划

## 项目信息
- 项目名称：
- 素材文件：
- 创建时间：

## 任务列表
按顺序列出所有 page，每项包含：
- page编号（如 page01）
- 页面主题
- 核心内容要点（3-5条）
- 预计复杂度

## 技术方案
- 框架选择
- 动画方案
- 响应式策略
```

### 2. page-design-guide.md
```markdown
# 页面设计指南

## page01
- 主题：
- 视觉风格：
- 动画入场顺序：标题 → 主角 → 配角 → 装饰
- 间距基准值：Xpx
- 特殊要求：

## page02
...
```

### 3. index.html
基础 HTML 骨架，包含所有 page 的 `<section>` 占位符。

## 工作流程
1. 读取 `SCRIPT_FILE`（**不读内容**，仅确认文件存在）
2. 读取设计规范 `dg-gray-slide-design-skill.md`
3. 生成 `dev-plan.md`
4. 生成 `page-design-guide.md`
5. 生成 `index.html`（基础骨架）
6. 返回三个文件的绝对路径

## 约束
- **不读素材文件内容**，只传递路径给后续 Agent
- 每个 page 的设计指南需包含动画入场顺序和间距基准值
- index.html 使用单文件模式，内联 CSS 和 JS

## 返回格式
```
dev-plan.md: {绝对路径}
page-design-guide.md: {绝对路径}
index.html: {绝对路径}
```
