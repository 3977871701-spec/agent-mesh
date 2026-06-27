# 编程项目工作流 - Agent Mesh 配置

## 概述
基于调度型主 Agent + 多专业子 Agent 的编程任务执行框架。

## Agent 角色定义

| Agent | 角色 | 模型 | 职责 |
|-------|------|------|------|
| dg-planner | 计划制定 | MiniMax-M2.7 | 分析需求，制定开发计划 |
| dg-dev | 开发工程师 | MiniMax-M2.7 | 编写代码，修复 bug，沉淀经验 |
| dg-frontend-test | 前端测试 | MiniMax-M2.7 | 前端布局、后端端口测试 |
| dg-backend | 后端工程师 | MiniMax-M2.7 | 后端任务设计，链接前端与端口 |
| dg-port | 端口工程师 | MiniMax-M2.7 | 制作 API 端口，配置前后端连接 |
| dg-webapp-test | 网页/App 测试 | MiniMax-M2.7 | 多次测试，检查 bug 和交互 |

## 核心原则
1. 主 Agent 只调度不干活
2. 保持上下文整洁
3. 及时记录日志
4. 主动反馈进展
5. 修正循环复用同一 DEV_ID

## 文件结构
```
workflows/programming/
├── MANIFEST.md          # 本文件
├── dg-planner.md        # 计划 Agent 配置
├── dg-dev.md            # 开发 Agent 配置
├── dg-frontend-test.md  # 前端测试 Agent 配置
├── dg-backend.md        # 后端 Agent 配置
├── dg-port.md           # 端口 Agent 配置
├── dg-webapp-test.md    # 网页/App 测试 Agent 配置
└── main-log.md          # 日志文件（自动生成）
```
