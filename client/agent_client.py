"""Agent客户端SDK"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable, List
import websockets

logger = logging.getLogger(__name__)


class AgentClient:
    """Agent客户端SDK"""

    def __init__(self, agent_id: str, name: str, agent_type: str = "custom"):
        self.agent_id = agent_id
        self.name = name
        self.agent_type = agent_type
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.message_handlers: Dict[str, List[Callable]] = {}
        self._receive_task: Optional[asyncio.Task] = None

    async def connect(self, ws_url: str = "ws://localhost:18800") -> bool:
        """连接到Agent Mesh服务器"""
        try:
            self.ws = await websockets.connect(ws_url)
            self.connected = True

            # 注册
            await self._send({
                "type": "register",
                "payload": {
                    "id": self.agent_id,
                    "name": self.name,
                    "type": self.agent_type
                }
            })

            # 启动接收循环
            self._receive_task = asyncio.create_task(self._receive_loop())

            logger.info(f"Connected to {ws_url}")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    async def disconnect(self):
        """断开连接"""
        self.connected = False
        if self._receive_task:
            self._receive_task.cancel()
        if self.ws:
            await self.ws.close()

    async def send_message(self, to: str, text: str, metadata: Optional[Dict] = None) -> bool:
        """发送消息"""
        return await self._send({
            "type": "message",
            "from": self.agent_id,
            "to": to,
            "payload": {"text": text},
            "metadata": metadata or {}
        })

    async def broadcast(self, text: str, target: str = "*") -> bool:
        """广播消息"""
        return await self._send({
            "type": "broadcast",
            "from": self.agent_id,
            "to": target,
            "payload": {"text": text}
        })

    async def create_task(
        self,
        to: str,
        title: str,
        description: str = "",
        priority: str = "normal"
    ) -> bool:
        """创建任务"""
        return await self._send({
            "type": "task",
            "from": self.agent_id,
            "to": to,
            "payload": {
                "title": title,
                "description": description,
                "priority": priority
            }
        })

    async def update_task(self, task_id: str, status: str, result: Optional[Dict] = None) -> bool:
        """更新任务状态"""
        return await self._send({
            "type": "task_update",
            "from": self.agent_id,
            "payload": {
                "task_id": task_id,
                "status": status,
                "result": result
            }
        })

    async def _send(self, data: Dict[str, Any]) -> bool:
        """发送原始消息"""
        if not self.ws or not self.connected:
            return False
        try:
            await self.ws.send(json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Send error: {e}")
            return False

    async def _receive_loop(self):
        """接收消息循环"""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid message: {message}")
        except websockets.exceptions.ConnectionClosed:
            self.connected = False
        except asyncio.CancelledError:
            pass

    async def _handle_message(self, data: Dict[str, Any]):
        """处理收到的消息"""
        msg_type = data.get("type")

        # 调用注册的处理器
        handlers = self.message_handlers.get(msg_type, [])
        for handler in handlers:
            try:
                await handler(data)
            except Exception as e:
                logger.error(f"Handler error: {e}")

    def on(self, msg_type: str, handler: Callable):
        """注册消息处理器"""
        if msg_type not in self.message_handlers:
            self.message_handlers[msg_type] = []
        self.message_handlers[msg_type].append(handler)

    async def wait_for_message(self, timeout: float = 30.0) -> Optional[Dict[str, Any]]:
        """等待下一条消息"""
        try:
            message = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
            return json.loads(message)
        except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
            return None

    async def run(self, ws_url: str = "ws://localhost:18800"):
        """运行客户端"""
        success = await self.connect(ws_url)
        if success:
            try:
                while self.connected:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                pass
            finally:
                await self.disconnect()


# 便捷函数
async def quick_send(
    agent_id: str,
    to: str,
    text: str,
    ws_url: str = "ws://localhost:18800"
) -> bool:
    """快速发送消息"""
    client = AgentClient(agent_id, agent_id)
    try:
        if await client.connect(ws_url):
            return await client.send_message(to, text)
        return False
    finally:
        await client.disconnect()


async def quick_receive(
    agent_id: str,
    ws_url: str = "ws://localhost:18800",
    timeout: float = 60.0
) -> Optional[Dict[str, Any]]:
    """快速接收消息"""
    client = AgentClient(agent_id, agent_id)
    try:
        if await client.connect(ws_url):
            return await client.wait_for_message(timeout)
        return None
    finally:
        await client.disconnect()
