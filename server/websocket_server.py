"""WebSocket服务器模块"""
import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Set, Optional, Callable, Any
import websockets
from websockets.server import WebSocketServerProtocol

from .models import Message, MessageType, Agent, AgentStatus
from .database import Database
from .config import ServerConfig

logger = logging.getLogger(__name__)


class WebSocketServer:
    def __init__(self, config: ServerConfig, database: Database):
        self.config = config
        self.db = database
        self.server = None
        # agent_id -> WebSocket连接
        self.connections: Dict[str, WebSocketServerProtocol] = {}
        # WebSocket -> agent_id
        self.ws_to_agent: Dict[WebSocketServerProtocol, str] = {}
        # 消息处理器
        self.message_handlers: Dict[MessageType, Callable] = {}
        # 运行状态
        self.running = False
        # 连接时间跟踪
        self.connection_times: Dict[str, datetime] = {}
        # 消息统计
        self.messages_sent = 0
        self.messages_received = 0
        # 监控任务
        self._monitor_task: Optional[asyncio.Task] = None

    def register_handler(self, msg_type: MessageType, handler: Callable):
        """注册消息处理器"""
        self.message_handlers[msg_type] = handler

    async def start(self):
        """启动WebSocket服务器"""
        self.server = await websockets.serve(
            self._handle_connection,
            self.config.host,
            self.config.port,
            max_size=10 * 1024 * 1024,  # 10MB
            ping_interval=self.config.heartbeat_interval,
            ping_timeout=self.config.heartbeat_timeout
        )
        self.running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"WebSocket server started on ws://{self.config.host}:{self.config.port}")

    async def stop(self):
        """停止WebSocket服务器"""
        self.running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        # 关闭所有连接
        for ws in list(self.connections.values()):
            await ws.close()
        self.connections.clear()
        self.ws_to_agent.clear()
        self.connection_times.clear()
        logger.info("WebSocket server stopped")

    async def _handle_connection(self, websocket: WebSocketServerProtocol):
        """处理新的WebSocket连接"""
        agent_id = None
        try:
            logger.info(f"New connection from {websocket.remote_address}")
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._process_message(websocket, data)
                except json.JSONDecodeError:
                    await self._send_error(websocket, "Invalid JSON")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await self._send_error(websocket, str(e))
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed: {agent_id}")
        finally:
            # 清理连接
            if websocket in self.ws_to_agent:
                agent_id = self.ws_to_agent[websocket]
                del self.ws_to_agent[websocket]
                if agent_id in self.connections:
                    del self.connections[agent_id]
                # 更新Agent状态为离线
                await self.db.update_agent_status(agent_id, AgentStatus.OFFLINE)
                # 通知其他Agent
                await self._broadcast_status(agent_id, AgentStatus.OFFLINE)

    async def _process_message(self, websocket: WebSocketServerProtocol, data: Dict[str, Any]):
        """处理收到的消息"""
        self.record_message_received()
        msg_type = data.get("type")

        # 注册消息
        if msg_type == "register":
            await self._handle_register(websocket, data)
            return

        # 心跳消息
        if msg_type == "heartbeat":
            await self._handle_heartbeat(websocket)
            return

        # 其他消息需要已注册
        agent_id = self.ws_to_agent.get(websocket)
        if not agent_id:
            await self._send_error(websocket, "Not registered")
            return

        # 创建消息对象
        message = Message.from_dict(data)
        message.from_agent = agent_id

        # 调用对应的处理器
        handler = self.message_handlers.get(MessageType(msg_type))
        if handler:
            await handler(message)
        else:
            await self._send_error(websocket, f"Unknown message type: {msg_type}")

    async def _handle_register(self, websocket: WebSocketServerProtocol, data: Dict[str, Any]):
        """处理Agent注册"""
        payload = data.get("payload", {})
        agent_id = payload.get("id") or str(uuid.uuid4())
        agent_name = payload.get("name", f"agent-{agent_id[:8]}")
        agent_type = payload.get("type", "custom")
        capabilities = payload.get("capabilities", [])

        # 检查是否已注册
        if agent_id in self.connections:
            # 断开旧连接
            old_ws = self.connections[agent_id]
            await old_ws.close()

        # 创建或更新Agent
        agent = Agent(
            id=agent_id,
            name=agent_name,
            type=agent_type,
            status=AgentStatus.ONLINE,
            capabilities=capabilities,
            endpoint=f"ws://{self.config.host}:{self.config.port}",
            last_seen=datetime.now()
        )
        await self.db.add_agent(agent)

        # 建立映射
        self.connections[agent_id] = websocket
        self.ws_to_agent[websocket] = agent_id
        self.connection_times[agent_id] = datetime.now()

        # 发送注册成功响应
        await self._send_message(websocket, {
            "type": "register_response",
            "id": str(uuid.uuid4()),
            "payload": {
                "agent_id": agent_id,
                "status": "success",
                "message": f"Agent {agent_name} registered successfully"
            }
        })

        # 通知其他Agent有新成员加入
        await self._broadcast_status(agent_id, AgentStatus.ONLINE)

        logger.info(f"Agent registered: {agent_id} ({agent_name})")

    async def _handle_heartbeat(self, websocket: WebSocketServerProtocol):
        """处理心跳"""
        agent_id = self.ws_to_agent.get(websocket)
        if agent_id:
            await self.db.update_agent_status(agent_id, AgentStatus.ONLINE)
        await self._send_message(websocket, {
            "type": "heartbeat_ack",
            "timestamp": datetime.now().isoformat()
        })

    async def _broadcast_status(self, agent_id: str, status: AgentStatus):
        """广播Agent状态变化"""
        message = {
            "type": "status_change",
            "id": str(uuid.uuid4()),
            "payload": {
                "agent_id": agent_id,
                "status": status.value,
                "timestamp": datetime.now().isoformat()
            }
        }
        await self.broadcast(message, exclude={agent_id})

    async def send_to_agent(self, agent_id: str, message: Dict[str, Any]) -> bool:
        """发送消息给指定Agent"""
        ws = self.connections.get(agent_id)
        if ws:
            await self._send_message(ws, message)
            self.record_message_sent()
            return True
        return False

    async def broadcast(self, message: Dict[str, Any], exclude: Optional[Set[str]] = None):
        """广播消息给所有在线Agent"""
        exclude = exclude or set()
        # 使用列表副本避免迭代中修改字典
        for aid, ws in list(self.connections.items()):
            if aid not in exclude:
                try:
                    await self._send_message(ws, message)
                    self.record_message_sent()
                except Exception as e:
                    logger.error(f"Error broadcasting to {aid}: {e}")

    async def _send_message(self, websocket: WebSocketServerProtocol, data: Dict[str, Any]):
        """发送消息"""
        try:
            await websocket.send(json.dumps(data))
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Connection already closed")

    async def _send_error(self, websocket: WebSocketServerProtocol, error: str):
        """发送错误消息"""
        await self._send_message(websocket, {
            "type": "error",
            "id": str(uuid.uuid4()),
            "payload": {"error": error}
        })

    def get_online_agents(self) -> Set[str]:
        """获取所有在线Agent ID"""
        return set(self.connections.keys())

    def is_agent_online(self, agent_id: str) -> bool:
        """检查Agent是否在线"""
        return agent_id in self.connections

    def get_agent_count(self) -> int:
        """获取在线Agent数量"""
        return len(self.connections)

    def get_server_stats(self) -> Dict[str, Any]:
        """获取服务器统计信息"""
        return {
            "online_count": len(self.connections),
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "uptime": self._get_uptime(),
            "connections": [
                {
                    "agent_id": aid,
                    "connected_at": self.connection_times.get(aid, datetime.now()).isoformat(),
                    "duration_seconds": (datetime.now() - self.connection_times.get(aid, datetime.now())).total_seconds()
                }
                for aid in self.connections.keys()
            ]
        }

    def _get_uptime(self) -> float:
        """获取服务器运行时长（秒）"""
        return (datetime.now() - self.start_time).total_seconds() if hasattr(self, 'start_time') else 0

    async def _monitor_loop(self):
        """监控循环 - 检测异常连接"""
        # 跟踪已警告过的agent，避免重复警告
        warned_agents: set = set()
        while self.running:
            try:
                await asyncio.sleep(300)  # 每5分钟检查一次
                # 检测长期未活跃的连接
                now = datetime.now()
                for agent_id, conn_time in list(self.connection_times.items()):
                    idle_seconds = (now - conn_time).total_seconds()
                    # 只对非console agent发出一次警告
                    if idle_seconds > self.config.heartbeat_timeout and agent_id != "console" and agent_id not in warned_agents:
                        logger.warning(f"Agent {agent_id} idle for {idle_seconds:.0f}s, may be disconnected")
                        warned_agents.add(agent_id)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")

    def record_message_sent(self):
        """记录发送的消息"""
        self.messages_sent += 1

    def record_message_received(self):
        """记录接收的消息"""
        self.messages_received += 1
