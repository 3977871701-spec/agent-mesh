# Agent Mesh

## 项目简介

Agent Mesh 是一个多 Agent 通信与协作平台，用于将不同类型的 AI Agent（如 OpenClaw、Hermes、Codex、Claude Code 等）统一接入同一个通信网络，实现 Agent 之间的消息传递、任务分发、状态监控和群组协作。

系统以 WebSocket 为核心通信协议，配合 SQLite 持久化存储和 FastAPI Web 管理界面，提供完整的 Agent 生命周期管理能力。通过桥接器（Bridge）和适配器（Adapter）机制，可以无缝连接外部 Agent 系统（如 OpenClaw Gateway），实现跨系统的 Agent 互操作。

## 功能特性

- **多 Agent 接入** — 支持 OpenClaw、Hermes、Codex、Claude Code、Phoenix 等多种 Agent 类型的统一接入
- **自动发现与注册** — 自动扫描 `~/.openclaw/`、`~/.hermes/`、`~/.codex/` 等目录，发现本地 Agent 并引导确认注册
- **实时消息通信** — 基于 WebSocket 的点对点消息、广播消息、群组消息，支持离线消息队列
- **任务引擎** — 创建、分配、追踪、完成任务，支持优先级设置、状态流转和任务重分配
- **OpenClaw 桥接** — 通过 JSON-RPC 协议与 OpenClaw Gateway 连接，支持 challenge-response 认证，实现跨系统消息转发
- **Web 管理界面** — 基于 FastAPI 的 REST API 和 Web 控制台，支持 Agent 管理、消息查看、状态监控
- **命令行工具** — 基于 Click + Rich 的 CLI，支持注册、发消息、创建任务、监听消息、交互模式等操作
- **自动重连** — 适配器层支持指数退避自动重连，保证连接稳定性
- **心跳检测** — 定时心跳与超时检测，自动识别断连 Agent
- **群组管理** — 支持创建群组、管理成员、群发消息

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    Web 管理界面 (FastAPI)                  │
│                   http://127.0.0.1:18801                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ 消息路由  │  │   任务引擎    │  │  Agent 注册中心   │  │
│  │ Message   │  │   Task       │  │  Agent           │  │
│  │ Router    │  │   Engine     │  │  Registry        │  │
│  └─────┬────┘  └──────┬───────┘  └────────┬─────────┘  │
│        │              │                    │             │
│  ┌─────┴──────────────┴────────────────────┴──────────┐ │
│  │            WebSocket 服务器 (port 18800)            │ │
│  └─────────────────────┬──────────────────────────────┘ │
│                        │                                │
│  ┌─────────────────────┴──────────────────────────────┐ │
│  │              SQLite 数据库 (aiosqlite)              │ │
│  └────────────────────────────────────────────────────┘ │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                     桥接 / 适配层                        │
│  ┌────────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ OpenClaw Bridge│  │Hermes Adapter│  │  其他适配器   │  │
│  │ (JSON-RPC/WS)  │  │             │  │  (Codex等)   │  │
│  └───────┬────────┘  └──────┬──────┘  └──────┬──────┘  │
│          │                  │                 │          │
├──────────┼──────────────────┼─────────────────┼──────────┤
│          ▼                  ▼                 ▼          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │OpenClaw Agent│  │  Hermes Agent│  │  其他 Agent   │  │
│  │  CEO/CTO/... │  │              │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**核心模块：**

| 模块 | 文件 | 职责 |
|------|------|------|
| WebSocket 服务器 | `server/websocket_server.py` | 管理 Agent 连接、注册、心跳、消息收发 |
| 消息路由 | `server/message_router.py` | 点对点/广播/群组消息路由，离线队列，OpenClaw 桥接转发 |
| 任务引擎 | `server/task_engine.py` | 任务创建、分配、状态流转、超时清理 |
| Agent 注册中心 | `server/agent_registry.py` | Agent 发现、确认、注册、注销 |
| 数据库 | `server/database.py` | SQLite 异步持久化，Agent/消息/任务/群组 CRUD |
| 配置管理 | `server/config.py` | YAML 配置加载与管理 |
| 数据模型 | `server/models.py` | Agent、Message、Task、Group 等核心数据结构 |
| OpenClaw 桥接 | `adapters/openclaw_bridge.py` | 与 OpenClaw Gateway 的 JSON-RPC 通信 |
| 适配器基类 | `adapters/base.py` | 通用适配器抽象，自动重连、心跳、消息处理 |
| CLI 工具 | `client/cli.py` | 命令行交互工具 |
| 全局桥接器 | `bridges/global_bridge.py` | 独立进程，双向转发 OpenClaw 与 Agent Mesh 消息 |

## 目录结构

```
agent-mesh/
├── server/                    # 服务端核心
│   ├── main.py                # 服务器主入口 (AgentMeshServer)
│   ├── config.py              # 配置管理
│   ├── models.py              # 数据模型 (Agent, Message, Task, Group)
│   ├── database.py            # SQLite 数据库操作
│   ├── websocket_server.py    # WebSocket 服务器
│   ├── message_router.py      # 消息路由
│   ├── task_engine.py         # 任务引擎
│   └── agent_registry.py      # Agent 注册中心
├── client/                    # 客户端
│   ├── cli.py                 # CLI 命令行工具
│   ├── agent_client.py        # Agent 客户端
│   ├── mesh_agent_client.py   # Mesh Agent 客户端
│   ├── mesh_agent_runner.py   # Agent 运行器
│   └── simple_client.py       # 简单客户端示例
├── adapters/                  # Agent 适配器
│   ├── base.py                # 适配器基类 (自动重连)
│   ├── openclaw_bridge.py     # OpenClaw Gateway 桥接
│   ├── hermes.py              # Hermes 适配器
│   ├── openclaw.py            # OpenClaw 适配器
│   └── generic.py             # 通用适配器
├── bridges/                   # 桥接器
│   └── global_bridge.py       # 全局桥接器 (独立进程)
├── scripts/                   # 脚本工具
│   └── register_all_agents.py # 批量注册 Agent
├── tests/                     # 测试
│   └── test_integration.py    # 集成测试
├── web/                       # Web 前端
│   └── index.html             # 管理界面
├── skills/                    # Agent 技能定义
├── workflows/                 # 工作流模板
├── projects/                  # 子项目 (如 schematic-designer)
├── config.yaml                # 主配置文件
├── requirements.txt           # Python 依赖
├── start.sh                   # 启动脚本
└── README.md
```

## 安装方法

### 环境要求

- Python 3.9+
- macOS / Linux

### 安装步骤

```bash
# 1. 克隆项目
cd /path/to/your/projects
# (项目已存在于本地)

# 2. 进入项目目录
cd agent-mesh

# 3. 安装 Python 依赖
pip install -r requirements.txt

# 4. 创建必要的数据目录
mkdir -p data logs
```

### 依赖列表

| 包名 | 用途 |
|------|------|
| `websockets>=12.0` | WebSocket 服务器与客户端通信 |
| `aiosqlite>=0.19.0` | 异步 SQLite 数据库操作 |
| `pyyaml>=6.0` | YAML 配置文件解析 |
| `click>=8.0` | CLI 命令行框架 |
| `rich>=13.0` | CLI 终端美化输出 |
| `fastapi>=0.100.0` | Web REST API 框架 |
| `uvicorn>=0.23.0` | ASGI 服务器 |
| `aiohttp>=3.9.0` | 异步 HTTP 客户端 |

## 使用方法

### 启动服务器

```bash
# 方式一：使用启动脚本（推荐）
./start.sh

# 方式二：直接运行 Python 模块
python -m server.main
```

启动后：
- WebSocket 服务：`ws://127.0.0.1:18800`
- Web 管理界面：`http://127.0.0.1:18801`

### 使用 CLI 工具

```bash
# 查看服务器状态
python -m client.cli status

# 列出所有已注册 Agent
python -m client.cli agents

# 注册新 Agent
python -m client.cli register --name my-agent --type custom

# 发送消息
python -m client.cli send --from console --to openclaw-ceo --message "你好"

# 创建任务
python -m client.cli task --from console --to openclaw-cto --title "代码审查" --description "审查PR #42" --priority high

# 广播消息
python -m client.cli broadcast --from console --message "系统通知" --target "*"

# 查看消息历史
python -m client.cli history --agent openclaw-ceo

# 监听实时消息
python -m client.cli listen --agent console

# 交互模式（图形化菜单）
python -m client.cli interactive
```

### 启动全局桥接器

全局桥接器作为独立进程运行，双向转发 OpenClaw Gateway 与 Agent Mesh 之间的消息：

```bash
python bridges/global_bridge.py
```

### Web API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/agents` | 获取所有 Agent 列表 |
| GET | `/api/agents/pending` | 获取待确认 Agent |
| POST | `/api/agents/{id}/confirm` | 确认 Agent |
| POST | `/api/agents/{id}/reject` | 拒绝 Agent |
| POST | `/api/agents/confirm-all` | 确认所有待定 Agent |
| POST | `/api/agents/start-all` | 启动所有已确认 Agent |
| POST | `/api/agents/start` | 启动指定 Agent 终端 |
| POST | `/api/agents/stop-all` | 停止所有 Agent |
| GET | `/api/agents/{id}/detail` | 获取 Agent 详情 |
| POST | `/api/agents/{id}/ping` | Ping Agent |
| POST | `/api/agents/{id}/forward` | 转发消息到 OpenClaw Agent |
| POST | `/api/agents/register` | 手动注册 Agent |
| GET | `/api/stats` | 获取系统统计 |
| GET | `/api/tasks` | 获取任务列表 |
| GET | `/api/messages/{id}` | 获取 Agent 消息历史 |
| GET | `/api/messages/conversation/{a}/{b}` | 获取对话记录 |
| POST | `/api/messages/send` | 发送消息 |
| GET | `/api/sessions` | 获取 OpenClaw 会话状态 |
| GET | `/api/phoenix/status` | 获取 Phoenix 系统状态 |

### 配置说明

编辑 `config.yaml` 自定义各项参数：

```yaml
server:
  host: 127.0.0.1          # 监听地址
  port: 18800               # WebSocket 端口
  max_connections: 100      # 最大连接数
  heartbeat_interval: 30    # 心跳间隔 (秒)
  heartbeat_timeout: 90     # 心跳超时 (秒)

database:
  path: ./data/agent_mesh.db  # SQLite 数据库路径

discovery:
  auto_discover: true       # 是否自动发现 Agent
  scan_paths:               # 扫描路径
    - ~/.openclaw/agents/
    - ~/.hermes/
    - ~/.codex/
  confirm_required: true    # 新发现的 Agent 是否需要确认

adapters:
  hermes:
    enabled: true
    cli_path: ~/.hermes/cli
  openclaw:
    enabled: true
    gateway: ws://127.0.0.1:18790
    token: your-token-here

logging:
  level: INFO               # 日志级别
  file: ./logs/agent_mesh.log
  max_size: 10485760        # 日志文件最大大小 (10MB)
  backup_count: 5           # 日志备份数

web:
  enabled: true             # 是否启用 Web 管理界面
  host: 127.0.0.1
  port: 18801               # Web 端口
```

## 许可证

本项目为私有项目。
