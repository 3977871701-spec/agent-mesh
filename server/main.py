"""Agent Mesh Server 主入口"""
import asyncio
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from .config import Config
from .database import Database
from .websocket_server import WebSocketServer
from .message_router import MessageRouter
from .task_engine import TaskEngine
from .agent_registry import AgentRegistry
from .models import AgentStatus, MessageType, Message, Agent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/agent_mesh.log')
    ]
)
logger = logging.getLogger(__name__)


class AgentMeshServer:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = Config.load(config_path)
        self.db = Database(self.config.database.path)
        self.ws_server = WebSocketServer(self.config.server, self.db)
        self.message_router = MessageRouter(self.ws_server, self.db)
        self.task_engine = TaskEngine(self.ws_server, self.db)
        self.agent_registry = AgentRegistry(self.db, self.config.discovery)
        self.openclaw_bridge = None
        self.ws_server.openclaw_bridge = None  # Will be set after bridge creation
        self._shutdown_event = asyncio.Event()
        # 跟踪已启动的OpenClaw agent会话
        self.openclaw_sessions: Dict[str, dict] = {}

    async def start(self):
        """启动服务器"""
        logger.info("Starting Agent Mesh Server...")

        # 确保数据目录存在
        Path(self.config.database.path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.config.logging.file).parent.mkdir(parents=True, exist_ok=True)

        # 连接数据库
        await self.db.connect()
        logger.info("Database connected")

        # 初始化Agent注册中心
        await self.agent_registry.initialize()
        logger.info("Agent registry initialized")

        # 连接OpenClaw Gateway并注册所有agents
        await self._connect_openclaw_bridge()

        # 启动WebSocket服务器
        await self.ws_server.start()
        logger.info(f"WebSocket server listening on ws://{self.config.server.host}:{self.config.server.port}")

        # 启动任务引擎
        await self.task_engine.start()
        logger.info("Task engine started")

        # 启动Web服务器（如果启用）
        if self.config.web.enabled:
            await self._start_web_server()

        logger.info("Agent Mesh Server started successfully!")
        logger.info(f"Configuration: {self.config_path}")

        # 打印已发现的Agent
        pending = await self.agent_registry.get_pending_agents()
        if pending:
            logger.info(f"Found {len(pending)} pending agents to confirm:")
            for agent in pending:
                logger.info(f"  - {agent.id} ({agent.name}) [{agent.type}]")

        # 等待关闭信号
        await self._shutdown_event.wait()

    async def _connect_openclaw_bridge(self):
        """连接OpenClaw Gateway桥接"""
        try:
            from adapters.openclaw_bridge import OpenClawBridge
            # 从配置获取OpenClaw适配器设置
            openclaw_config = self.config.adapters.get("openclaw")
            gateway_url = "ws://127.0.0.1:18790"
            token = ""
            if openclaw_config:
                gateway_url = openclaw_config.gateway or gateway_url
                token = openclaw_config.token or token

            self.openclaw_bridge = OpenClawBridge(
                gateway_url=gateway_url,
                token=token
            )
            connected = await self.openclaw_bridge.connect()
            if connected:
                logger.info("OpenClaw bridge connected")
                # 设置bridge引用，以便message_router可以访问
                self.ws_server.openclaw_bridge = self.openclaw_bridge
                # 注册所有OpenClaw agents
                await self._register_openclaw_agents()
            else:
                logger.warning("OpenClaw bridge connection failed")
        except Exception as e:
            logger.warning(f"OpenClaw bridge not available: {e}")

    async def _register_openclaw_agents(self):
        """注册所有OpenClaw Agents到mesh"""
        if not self.openclaw_bridge:
            return

        openclaw_agents = [
            ("ceo", "CEO", ["management", "decision", "coordination"]),
            ("cto", "CTO", ["code", "architecture", "deployment"]),
            ("cfo", "CFO", ["finance", "budgeting", "analysis"]),
            ("coo", "COO", ["operations", "logistics", "management"]),
            ("cmo", "CMO", ["marketing", "branding", "communication"]),
            ("hr", "HR", ["recruitment", "personnel", "training"]),
            ("main", "Main", ["general", "coordination"]),
        ]

        for agent_id, name, capabilities in openclaw_agents:
            agent = Agent(
                id=f"openclaw-{agent_id}",
                name=name,
                type="openclaw",
                status=AgentStatus.OFFLINE,
                capabilities=capabilities,
                metadata={"source": "openclaw", "original_id": agent_id}
            )
            await self.db.add_agent(agent)
            logger.info(f"Registered OpenClaw agent: {agent_id}")

        # 设置消息转发 - 从OpenClaw收到的消息转发到WebSocket客户端
        if self.openclaw_bridge:
            self.openclaw_bridge.register_handler("session.message", self._forward_openclaw_message)

    async def _forward_openclaw_message(self, data: Dict):
        """转发OpenClaw消息到WebSocket"""
        # 处理 session.message 事件格式
        from_agent = data.get("from", "unknown")
        text = data.get("text", "")
        role = data.get("role", "")

        logger.info(f"_forward_openclaw_message: from={from_agent}, role={role}, text={str(text)[:50]}")

        # 只转发agent的回复，不转发用户消息
        if role and role != "assistant":
            logger.debug(f"Skipping {role} message from {from_agent}")
            return

        if not text:
            return

        # 创建消息对象
        full_from = f"openclaw-{from_agent}" if not from_agent.startswith("openclaw-") else from_agent
        message = Message(
            type=MessageType.MESSAGE,
            from_agent=full_from,
            to_agent="console",
            payload={"text": text, "source": "openclaw"}
        )
        await self.db.add_message(message)
        logger.info(f"Message saved to DB: {full_from} -> console")

        # 广播给所有连接的WebSocket客户端（包括console）
        await self.ws_server.broadcast({
            "type": "message",
            "from": full_from,
            "to": "console",
            "payload": {"text": text, "source": "openclaw"},
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"Message broadcast to WebSocket")

    async def stop(self):
        """停止服务器"""
        logger.info("Shutting down Agent Mesh Server...")

        # 停止任务引擎
        await self.task_engine.stop()

        # 停止WebSocket服务器
        await self.ws_server.stop()

        # 关闭数据库
        await self.db.close()

        logger.info("Agent Mesh Server stopped")

    async def _start_web_server(self):
        """启动Web管理服务器"""
        try:
            from fastapi import FastAPI
            from fastapi.staticfiles import StaticFiles
            from fastapi.responses import FileResponse
            import uvicorn

            app = FastAPI(title="Agent Mesh Admin")

            # 静态文件
            web_dir = Path(__file__).parent.parent / "web"
            if web_dir.exists():
                app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

            @app.get("/")
            async def index():
                return FileResponse(str(web_dir / "index.html"))

            @app.get("/api/agents")
            async def get_agents():
                agents = await self.agent_registry.get_all_agents()
                return {"agents": [a.to_dict() for a in agents]}

            @app.get("/api/agents/pending")
            async def get_pending_agents():
                agents = await self.agent_registry.get_pending_agents()
                return {"agents": [a.to_dict() for a in agents]}

            @app.post("/api/agents/{agent_id}/confirm")
            async def confirm_agent(agent_id: str):
                agent = await self.agent_registry.confirm_agent(agent_id)
                if agent:
                    return {"status": "ok", "agent": agent.to_dict()}
                return {"status": "error", "message": "Agent not found"}

            @app.post("/api/agents/{agent_id}/reject")
            async def reject_agent(agent_id: str):
                success = await self.agent_registry.reject_agent(agent_id)
                return {"status": "ok" if success else "error"}

            @app.post("/api/agents/confirm-all")
            async def confirm_all_agents():
                """确认所有待定Agent"""
                pending = await self.agent_registry.get_pending_agents()
                confirmed = []
                for agent in pending:
                    confirmed_agent = await self.agent_registry.confirm_agent(agent.id)
                    if confirmed_agent:
                        confirmed.append(confirmed_agent.id)
                return {"status": "ok", "confirmed": confirmed, "count": len(confirmed)}

            @app.post("/api/agents/start-all")
            async def start_all_agents():
                """启动所有已确认的Agent（发送广播消息）"""
                agents = await self.agent_registry.get_all_agents()
                started = []
                for agent in agents:
                    if agent.status != AgentStatus.ONLINE:
                        await self.agent_registry.update_agent_status(agent.id, AgentStatus.ONLINE)
                        started.append(agent.id)
                # 广播启动消息
                await self.ws_server.broadcast({
                    "type": "broadcast",
                    "from": "console",
                    "payload": {"action": "start_all", "initiated_by": "console"}
                })
                return {"status": "ok", "started": started, "count": len(started)}

            @app.get("/api/stats")
            async def get_stats():
                return {
                    "agents": self.agent_registry.get_registry_stats(),
                    "online_count": self.ws_server.get_agent_count(),
                    "queue_size": self.message_router.get_queue_size(),
                    "task_count": len(await self.db.get_all_tasks())
                }

            @app.get("/api/tasks")
            async def get_tasks():
                tasks = await self.db.get_all_tasks()
                return {"tasks": [t.to_dict() for t in tasks]}

            @app.post("/api/agents/register")
            async def register_agent(request: dict):
                agent = await self.agent_registry.register_agent(
                    agent_id=request.get("id"),
                    name=request.get("name", ""),
                    agent_type=request.get("type", "custom"),
                    capabilities=request.get("capabilities", []),
                    metadata=request.get("metadata", {})
                )
                return agent.to_dict()

            @app.get("/api/messages/{agent_id}")
            async def get_messages(agent_id: str):
                messages = await self.db.get_messages(agent_id)
                msg_list = messages[-50:] if len(messages) > 50 else messages
                return {"messages": [m.to_dict() for m in msg_list]}

            @app.get("/api/messages/conversation/{agent1}/{agent2}")
            async def get_conversation(agent1: str, agent2: str):
                messages = await self.db.get_conversation(agent1, agent2)
                msg_list = messages[-50:] if len(messages) > 50 else messages
                return {"messages": [m.to_dict() for m in msg_list]}

            @app.post("/api/messages/send")
            async def send_message(request: dict):
                from_agent = request.get("from", "console")
                to_agent = request.get("to", "")
                text = request.get("text", "")
                if not to_agent or not text:
                    return {"status": "error", "message": "to and text are required"}
                msg = await self.message_router.send_message(
                    from_agent=from_agent,
                    to_agent=to_agent,
                    payload={"text": text},
                    metadata=request.get("metadata", {})
                )
                return {"status": "ok", "message": msg.to_dict()}

            @app.get("/api/agents/{agent_id}/detail")
            async def get_agent_detail(agent_id: str):
                """获取Agent详细信息"""
                agent = await self.agent_registry.get_agent(agent_id)
                if not agent:
                    return {"status": "error", "message": "Agent not found"}
                is_online = self.ws_server.is_agent_online(agent_id)
                stats = self.ws_server.get_server_stats()
                connection_info = None
                for conn in stats.get("connections", []):
                    if conn.get("agent_id") == agent_id:
                        connection_info = conn
                        break
                return {
                    "status": "ok",
                    "agent": agent.to_dict(),
                    "is_online": is_online,
                    "connection_info": connection_info,
                    "offline_reason": "Agent未连接服务器" if not is_online else None
                }

            @app.post("/api/agents/{agent_id}/ping")
            async def ping_agent(agent_id: str):
                """Ping Agent检查连接状态"""
                is_online = self.ws_server.is_agent_online(agent_id)
                if is_online:
                    await self.ws_server.send_to_agent(agent_id, {
                        "type": "ping",
                        "from": "console",
                        "payload": {"action": "ping", "initiated_by": "console"}
                    })
                    return {"status": "ok", "online": True, "message": "Ping sent"}
                else:
                    return {"status": "ok", "online": False, "message": "Agent is offline"}

            @app.post("/api/agents/start")
            async def start_agent(request: dict):
                """启动指定Agent的终端"""
                agent_id = request.get("agent_id")
                agent_type = request.get("agent_type", "custom")
                if not agent_id:
                    return {"status": "error", "message": "agent_id required"}

                success = False
                message = ""

                try:
                    import subprocess

                    # OpenClaw agents - 通过Terminal打开
                    if agent_type == "openclaw" or "openclaw" in agent_id:
                        original_id = agent_id.replace("openclaw-", "")
                        # OpenClaw uses 'tui' command to open interactive terminal
                        script = f'tell app "Terminal" to do script "openclaw tui --session {original_id}"'
                        subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
                        success = True
                        message = f"已在Terminal中启动 {agent_id}"
                        # 跟踪会话
                        self.openclaw_sessions[original_id] = {
                            "status": "launched",
                            "launched_at": datetime.now().isoformat(),
                            "connected_at": None
                        }

                    # Hermes agent
                    elif agent_type == "hermes" or agent_id == "hermes-brain":
                        cmd = 'tell app "Terminal" to do script "hermes chat"'
                        subprocess.run(["osascript", "-e", cmd], check=True, capture_output=True)
                        success = True
                        message = f"已在Terminal中启动 Hermes"

                    # Claude Code
                    elif agent_type == "claude":
                        cmd = f'tell app "Terminal" to do script "claude"'
                        subprocess.run(["osascript", "-e", cmd], check=True, capture_output=True)
                        success = True
                        message = f"已在Terminal中启动 Claude Code"

                    # Phoenix
                    elif agent_type == "phoenix" or agent_id == "phoenix-router":
                        cmd = f'tell app "Terminal" to do script "cd ~/Projects/不死鸟/phoenix-v5.1.1-release/phoenix-v5.1.1-release && echo \\"Phoenix启动中...\\""'
                        subprocess.run(["osascript", "-e", cmd], check=True, capture_output=True)
                        success = True
                        message = f"已在Terminal中打开 Phoenix"

                    # Codex
                    elif agent_type == "codex":
                        cmd = 'tell app "Terminal" to do script "codex"'
                        subprocess.run(["osascript", "-e", cmd], check=True, capture_output=True)
                        success = True
                        message = f"已在Terminal中启动 Codex"

                    # 自定义/其他
                    else:
                        cmd = f'tell app "Terminal" to do script "echo \\"启动 {agent_id}...\\""'
                        subprocess.run(["osascript", "-e", cmd], check=True, capture_output=True)
                        success = True
                        message = f"已在Terminal中打开 {agent_id}"

                except subprocess.CalledProcessError as e:
                    message = f"启动失败: Terminal命令执行错误"
                except Exception as e:
                    message = f"启动失败: {str(e)}"
                    logger.error(f"Start agent error: {e}")

                return {"status": "ok" if success else "error", "success": success, "message": message}

            @app.post("/api/agents/stop-all")
            async def stop_all_agents():
                """停止所有Agent连接"""
                # 广播停止消息
                await self.ws_server.broadcast({
                    "type": "shutdown",
                    "from": "console",
                    "payload": {"action": "stop_all"}
                })
                return {"status": "ok", "message": "停止命令已广播"}

            @app.get("/api/sessions")
            async def get_sessions():
                """获取所有OpenClaw会话状态"""
                return {"sessions": self.openclaw_sessions}

            @app.get("/api/sessions/{agent_id}")
            async def get_session(agent_id: str):
                """获取指定Agent的会话状态"""
                session = self.openclaw_sessions.get(agent_id)
                if session:
                    return {"status": "ok", "session": session}
                return {"status": "error", "message": "Session not found"}

            @app.get("/api/phoenix/status")
            async def phoenix_status():
                """获取不死鸟(Phoenix)系统状态"""
                phoenix_path = Path.home() / "Projects" / "不死鸟" / "phoenix-v5.1.1-release" / "phoenix-v5.1.1-release" / "config.json"
                status = {
                    "installed": phoenix_path.exists(),
                    "path": str(phoenix_path),
                    "version": "5.1.1",
                    "config": None
                }
                if phoenix_path.exists():
                    try:
                        import json
                        with open(phoenix_path) as f:
                            config = json.load(f)
                            status["config"] = {
                                "routing_enabled": config.get("router", {}).get("enabled", False),
                                "memory_enabled": config.get("memory", {}).get("enabled", False),
                                "cost_limit_daily": config.get("executor", {}).get("budget", {}).get("daily_limit_usd", 0),
                                "cost_limit_monthly": config.get("executor", {}).get("budget", {}).get("monthly_limit_usd", 0),
                            }
                    except:
                        pass
                return status

            @app.post("/api/agents/{agent_id}/forward")
            async def forward_to_agent(agent_id: str, request: dict):
                """转发消息到OpenClaw Agent"""
                message = request.get("message", "")
                if not message:
                    return {"status": "error", "message": "message required"}

                # 如果有OpenClaw bridge，发送消息
                if self.openclaw_bridge and self.openclaw_bridge.is_connected():
                    # 提取原始agent ID (去掉openclaw-前缀)
                    original_id = agent_id.replace("openclaw-", "")
                    success = await self.openclaw_bridge.send_to_agent(original_id, {
                        "type": "message",
                        "text": message,
                        "from": "console"
                    })
                    return {"status": "ok", "forwarded": success}
                else:
                    return {"status": "ok", "forwarded": False, "message": "OpenClaw bridge not connected"}

            @app.get("/api/systems")
            async def get_all_systems():
                """获取所有系统状态"""
                systems = []

                # Agent Mesh
                systems.append({
                    "name": "Agent Mesh",
                    "type": "mesh",
                    "status": "running",
                    "url": f"http://localhost:{self.config.web.port}",
                    "agents_count": len(await self.agent_registry.get_all_agents())
                })

                # OpenClaw Gateway
                try:
                    import subprocess
                    result = subprocess.run(["lsof", "-i", ":18790"], capture_output=True, text=True)
                    gateway_online = result.returncode == 0 and "LISTEN" in result.stdout
                except:
                    gateway_online = False

                systems.append({
                    "name": "OpenClaw Gateway",
                    "type": "gateway",
                    "status": "running" if gateway_online else "stopped",
                    "port": 18790
                })

                # Hermes
                try:
                    result = subprocess.run(["pgrep", "-f", "hermes.*chat"], capture_output=True, text=True)
                    hermes_online = result.returncode == 0
                except:
                    hermes_online = False

                systems.append({
                    "name": "Hermes",
                    "type": "hermes",
                    "status": "running" if hermes_online else "stopped"
                })

                # Phoenix
                phoenix_path = Path.home() / "Projects" / "不死鸟" / "phoenix-v5.1.1-release" / "phoenix-v5.1.1-release" / "config.json"
                systems.append({
                    "name": "Phoenix (不死鸟)",
                    "type": "phoenix",
                    "status": "installed" if phoenix_path.exists() else "not_found",
                    "version": "5.1.1"
                })

                # Codex
                try:
                    result = subprocess.run(["pgrep", "-f", "codex.*app-server"], capture_output=True, text=True)
                    codex_online = result.returncode == 0
                except:
                    codex_online = False

                systems.append({
                    "name": "Codex",
                    "type": "codex",
                    "status": "running" if codex_online else "stopped"
                })

                return {"systems": systems}

            # 在后台启动uvicorn
            config = uvicorn.Config(
                app,
                host=self.config.web.host,
                port=self.config.web.port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            asyncio.create_task(server.serve())
            logger.info(f"Web server listening on http://{self.config.web.host}:{self.config.web.port}")

        except ImportError:
            logger.warning("FastAPI/uvicorn not installed, web server disabled")

    def shutdown(self):
        """触发关闭"""
        self._shutdown_event.set()


async def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    server = AgentMeshServer(config_path)

    # 处理信号
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, server.shutdown)

    try:
        await server.start()
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
