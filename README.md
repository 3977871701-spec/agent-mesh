# Agent Mesh - 统一Agent通信平台

一个本地部署的Agent通信系统，让所有AI Agent能够相互通信、协作。

## 特性

- **WebSocket实时通信** - 低延迟双向通信
- **自动发现** - 自动扫描并发现已有的Agent系统
- **适配器模式** - 为Hermes、OpenClaw、Codex等系统提供统一接口
- **点对点消息** - Agent之间直接通信
- **广播/群组消息** - 支持广播和群组消息
- **任务分发追踪** - 创建、分配、追踪任务状态
- **消息持久化** - SQLite存储所有消息历史
- **Web管理界面** - 直观的Web控制台
- **CLI工具** - 命令行管理工具

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Mesh Server                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ WebSocket│  │  Agent   │  │  Message │  │   Task   │    │
│  │  Server  │  │ Registry │  │  Router  │  │  Engine  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│                     SQLite Database                          │
└─────────────────────────────────────────────────────────────┘
           │            │            │            │
    ┌──────┴──┐  ┌──────┴──┐  ┌──────┴──┐  ┌──────┴──┐
    │  Hermes │  │ OpenClaw│  │  Codex  │  │ Custom  │
    │ Adapter │  │ Adapter │  │ Adapter │  │ Adapter │
    └─────────┘  └─────────┘  └─────────┘  └─────────┘
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务器

```bash
./start.sh
```

或者手动启动：

```bash
python -m server.main
```

### 3. 访问Web界面

打开浏览器访问: http://127.0.0.1:18801

### 4. 启动Agent

在Web界面中：
- 点击 **▶ 全部启动** 按钮启动所有离线Agent
- 或者点击单个Agent旁边的 **▶** 按钮启动单个Agent

或者使用命令行：

```bash
# 启动所有Agent
~/Scripts/launch_agents.sh start

# 查看状态
~/Scripts/launch_agents.sh status

# 停止所有Agent
~/Scripts/launch_agents.sh stop
```

### 5. 使用CLI工具

```bash
# 注册新Agent
python -m client.cli register --name my-agent --type custom

# 发送消息
python -m client.cli send --from agent-a --to agent-b --message "Hello"

# 创建任务
python -m client.cli task --from agent-a --to ceo --title "审查报告"

# 监听消息
python -m client.cli listen --agent my-agent

# 查看状态
python -m client.cli status
```

## 配置

配置文件: `config.yaml`

```yaml
server:
  host: 127.0.0.1
  port: 18800

database:
  path: ./data/agent_mesh.db

discovery:
  auto_discover: true
  scan_paths:
    - ~/.openclaw/agents/
    - ~/.hermes/
    - ~/.codex/

adapters:
  hermes:
    enabled: true
  openclaw:
    enabled: true
    gateway: ws://127.0.0.1:18790

web:
  enabled: true
  port: 18801
```

## 适配器

### Hermes适配器

集成Hermes AI Agent系统，作为"大脑"协调所有Agent。

### OpenClaw适配器

集成OpenClaw Agent集群（CEO、CTO、CFO等），复用现有WebSocket协议。

### 通用适配器

用于自定义Agent，提供基础通信能力。

## API

### WebSocket消息格式

```json
{
  "type": "message|task|broadcast|register|heartbeat",
  "id": "uuid",
  "from": "agent-id",
  "to": "agent-id",
  "payload": {},
  "metadata": {},
  "timestamp": "ISO-8601"
}
```

### HTTP API

- `GET /api/agents` - 获取所有Agent
- `GET /api/agents/pending` - 获取待确认Agent
- `POST /api/agents/{id}/confirm` - 确认Agent
- `POST /api/agents/{id}/reject` - 拒绝Agent
- `GET /api/stats` - 获取统计信息

## 目录结构

```
agent-mesh/
├── server/          # 服务器核心模块
│   ├── main.py      # 主入口
│   ├── config.py    # 配置管理
│   ├── database.py  # 数据库操作
│   ├── models.py    # 数据模型
│   ├── websocket_server.py  # WebSocket服务器
│   ├── message_router.py    # 消息路由
│   ├── task_engine.py       # 任务引擎
│   └── agent_registry.py    # Agent注册中心
├── adapters/        # 适配器
│   ├── base.py      # 基类
│   ├── generic.py   # 通用适配器
│   ├── openclaw.py  # OpenClaw适配器
│   └── hermes.py    # Hermes适配器
├── client/          # 客户端
│   ├── agent_client.py  # SDK
│   └── cli.py       # CLI工具
├── web/             # Web管理界面
├── data/            # 数据库文件
├── logs/            # 日志文件
├── config.yaml      # 配置文件
├── requirements.txt # 依赖
├── start.sh         # 启动脚本
└── README.md
```

## 技术栈

- **Python 3.9+**
- **WebSocket** (websockets库)
- **SQLite** (aiosqlite)
- **FastAPI** (Web API)
- **Click + Rich** (CLI)
- **PyYAML** (配置)

## License

MIT
