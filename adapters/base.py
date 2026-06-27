"""适配器基类 - 增强版"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import asyncio
import json
import logging
import websockets

from server.models import Message, MessageType, Agent, AgentStatus

logger = logging.getLogger(__name__)


class BaseAdapter(ABC):
    """Agent适配器基类 - 支持自动重连"""

    def __init__(self, agent_id: str, name: str, agent_type: str):
        self.agent_id = agent_id
        self.name = name
        self.agent_type = agent_type
        self.ws_url: Optional[str] = None
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.message_handlers: Dict[MessageType, List[Callable]] = {}
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        # 重连配置
        self._reconnect_enabled = True
        self._reconnect_delay = 1  # 初始延迟（秒）
        self._max_reconnect_delay = 60  # 最大延迟
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 10
        # 事件回调
        self._on_connect_callbacks: List[Callable] = []
        self._on_disconnect_callbacks: List[Callable] = []

    async def connect(self, ws_url: str) -> bool:
        """连接到Agent Mesh服务器"""
        self.ws_url = ws_url
        try:
            self.ws = await websockets.connect(
                ws_url,
                ping_interval=30,
                ping_timeout=90,
                close_timeout=10
            )
            self.connected = True
            self._reconnect_attempts = 0
            self._reconnect_delay = 1

            # 注册到服务器
            await self._register()

            # 启动心跳
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            # 启动接收循环
            self._receive_task = asyncio.create_task(self._receive_loop())

            # 启动重连监控
            self._reconnect_task = asyncio.create_task(self._reconnect_loop())

            # 触发连接回调
            for cb in self._on_connect_callbacks:
                try:
                    if asyncio.iscoroutinefunction(cb):
                        await cb(self)
                    else:
                        cb(self)
                except Exception as e:
                    logger.error(f"Connect callback error: {e}")

            logger.info(f"{self.name} connected to {ws_url}")
            return True

        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.connected = False
            return False

    async def disconnect(self, reason: str = "manual"):
        """断开连接"""
        self._reconnect_enabled = False
        self.connected = False

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._receive_task:
            self._receive_task.cancel()
        if self._reconnect_task:
            self._reconnect_task.cancel()

        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass

        logger.info(f"{self.name} disconnected: {reason}")

        # 触发断开回调
        for cb in self._on_disconnect_callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(self, reason)
                else:
                    cb(self, reason)
            except Exception as e:
                logger.error(f"Disconnect callback error: {e}")

    async def _reconnect_loop(self):
        """自动重连循环"""
        while self._reconnect_enabled:
            try:
                await asyncio.sleep(self._reconnect_delay)
                if not self.connected and self._reconnect_enabled:
                    if self._max_reconnect_attempts > 0 and self._reconnect_attempts >= self._max_reconnect_attempts:
                        logger.warning(f"{self.name}: Max reconnect attempts reached")
                        break

                    self._reconnect_attempts += 1
                    logger.info(f"{self.name}: Reconnect attempt {self._reconnect_attempts}")

                    if await self.connect(self.ws_url):
                        logger.info(f"{self.name}: Reconnected successfully")
                    else:
                        # 指数退避
                        self._reconnect_delay = min(
                            self._reconnect_delay * 2,
                            self._max_reconnect_delay
                        )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Reconnect loop error: {e}")

    async def _register(self):
        """注册到服务器"""
        await self.send_raw({
            "type": "register",
            "payload": {
                "id": self.agent_id,
                "name": self.name,
                "type": self.agent_type,
                "capabilities": self.get_capabilities()
            }
        })

    async def send_message(self, to: str, payload: Dict[str, Any], metadata: Optional[Dict] = None) -> bool:
        """发送消息给指定Agent"""
        message = {
            "type": "message",
            "id": str(datetime.now().timestamp()),
            "from": self.agent_id,
            "to": to,
            "payload": payload,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        return await self.send_raw(message)

    async def broadcast(self, target: str, payload: Dict[str, Any], metadata: Optional[Dict] = None) -> bool:
        """广播消息"""
        message = {
            "type": "broadcast",
            "id": str(datetime.now().timestamp()),
            "from": self.agent_id,
            "to": target,
            "payload": payload,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        return await self.send_raw(message)

    async def send_task(self, to: str, title: str, description: str = "", priority: str = "normal") -> bool:
        """发送任务"""
        message = {
            "type": "task",
            "id": str(datetime.now().timestamp()),
            "from": self.agent_id,
            "to": to,
            "payload": {
                "title": title,
                "description": description,
                "priority": priority
            },
            "timestamp": datetime.now().isoformat()
        }
        return await self.send_raw(message)

    async def update_task(self, task_id: str, status: str, result: Optional[Dict] = None) -> bool:
        """更新任务状态"""
        message = {
            "type": "task_update",
            "id": str(datetime.now().timestamp()),
            "from": self.agent_id,
            "payload": {
                "task_id": task_id,
                "status": status,
                "result": result
            },
            "timestamp": datetime.now().isoformat()
        }
        return await self.send_raw(message)

    async def send_raw(self, data: Dict[str, Any]) -> bool:
        """发送原始消息"""
        if not self.ws or not self.connected:
            return False
        try:
            await self.ws.send(json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Send error: {e}")
            self.connected = False
            return False

    async def _receive_loop(self):
        """接收消息循环"""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON: {message}")
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"Connection closed: {e}")
            self.connected = False
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Receive loop error: {e}")
            self.connected = False

    async def _handle_message(self, data: Dict[str, Any]):
        """处理收到的消息"""
        msg_type = data.get("type")

        # 注册响应
        if msg_type == "register_response":
            await self.on_registered(data.get("payload", {}))
            return

        # 心跳响应
        if msg_type == "heartbeat_ack":
            return

        # 状态变化通知
        if msg_type == "status_change":
            await self.on_status_change(data.get("payload", {}))
            return

        # 错误消息
        if msg_type == "error":
            await self.on_error(data.get("payload", {}).get("error", "Unknown error"))
            return

        # 转换为Message对象
        message = Message.from_dict(data)

        # 调用注册的处理器
        handlers = self.message_handlers.get(message.type, [])
        for handler in handlers:
            try:
                await handler(message)
            except Exception as e:
                logger.error(f"Handler error: {e}")

        # 调用通用处理器
        await self.on_message(message)

    async def _heartbeat_loop(self):
        """心跳循环"""
        try:
            while self.connected:
                await asyncio.sleep(30)
                if self.connected:
                    success = await self.send_raw({"type": "heartbeat"})
                    if not success:
                        logger.warning("Heartbeat failed, connection may be lost")
                        self.connected = False
                        break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")

    def on_connect(self, callback: Callable):
        """注册连接成功回调"""
        self._on_connect_callbacks.append(callback)

    def on_disconnect(self, callback: Callable):
        """注册断开连接回调"""
        self._on_disconnect_callbacks.append(callback)

    def register_handler(self, msg_type: MessageType, handler: Callable):
        """注册特定类型消息处理器"""
        if msg_type not in self.message_handlers:
            self.message_handlers[msg_type] = []
        self.message_handlers[msg_type].append(handler)

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """获取Agent能力列表"""
        return []

    @abstractmethod
    async def on_message(self, message: Message):
        """处理收到的消息（子类实现）"""
        pass

    async def on_registered(self, data: Dict[str, Any]):
        """注册成功回调"""
        logger.info(f"Registered: {data}")

    async def on_status_change(self, data: Dict[str, Any]):
        """状态变化回调"""
        logger.info(f"Status change: {data}")

    async def on_error(self, error: str):
        """错误回调"""
        logger.error(f"Error: {error}")

    async def run(self, ws_url: str = "ws://localhost:18800"):
        """运行适配器（自动重连）"""
        self._reconnect_enabled = True

        while self._reconnect_enabled:
            success = await self.connect(ws_url)
            if success:
                logger.info(f"{self.name} running on {ws_url}")
                try:
                    while self.connected:
                        await asyncio.sleep(1)
                except asyncio.CancelledError:
                    break
            else:
                # 连接失败，等待重连
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)

        await self.disconnect("run ended")
