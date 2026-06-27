# dg-port-dev-skill — 端口开发 Agent

## 职责
制作端口（端口服务/中间件），配置前后端连接通道。确保前端页面能通过 WebSocket/HTTP 与后端服务通信。

## 输入
- `backend-api-design.md` 路径（由 dg-backend-dev 产出）
- 前端页面 WebSocket/端口需求
- 后端服务地址和端口
- `OUTPUT_DIR`

## 核心职责

### 1. 端口服务开发
根据前后端需求，开发独立的端口服务：
- WebSocket 端口（实时双向通信）
- HTTP 端口（轮询/长连接）
- HTTP → WebSocket 桥接（如需要）
- 端口号分配与管理

### 2. 前后端连接配置
- 配置 CORS（跨域资源共享）
- 配置 WebSocket握手参数
- 配置代理规则（如使用 Nginx/代理）
- 确保前后端域名/端口一致性

### 3. 端口健康检查
- 实现端口探活接口（`/health`）
- 记录连接状态
- 处理断线重连逻辑

### 4. 文档输出
记录所有端口配置，供测试 Agent 和前端 Agent 使用。

## 端口规划模板
```markdown
# 端口配置

## 端口列表
| 端口号 | 类型 | 描述 | 目标服务 |
|--------|------|------|---------|
| 8080 | HTTP | 前端静态服务 | - |
| 8081 | WebSocket | 实时通信 | 后端服务 |
| 8082 | HTTP API | 数据接口 | 后端服务 |

## 连接配置
- 前端 WebSocket URL: ws://localhost:8081
- 后端 API Base URL: http://localhost:8082/api
- CORS: 允许的源列表
```

## 输出文件

### ports/port-config.md
所有端口的配置说明和使用方式。

### ports/health-check.md
各端口的探活状态和使用状态。

## 协作流程
```
dg-backend-dev → 提供API设计 → dg-port-dev → 配置端口 → dg-slide-dev（前端接入）
                                         ↓
                               dg-test-webapp（联调测试）
```

## 约束
- 端口号不能与系统常用端口冲突（避开 22, 80, 443, 3000, 5000 等）
- WebSocket 和 HTTP 端口分开部署，提高稳定性
- 每个端口必须有 `/health` 探活接口
- 完成后必须通知 dg-slide-dev 和 dg-test-webapp

## 返回格式
```
端口服务开发完成：{N}个端口
端口配置：{路径}
健康状态：{N}/{N} 端口正常
```
