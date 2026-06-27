"""OpenClaw适配器 - 集成OpenClaw Agent系统"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
import websockets

from .base import BaseAdapter
from server.models import Message, MessageType

logger = logging.getLogger(__name__)


class OpenClawAdapter(BaseAdapter):
    """OpenClaw Agent适配器"""

    def __init__(
        self,
        agent_name: str,
        gateway_url: str = "ws://127.0.0.1:18790",
        token: str = ""
    ):
        super().__init__(f"openclaw-{agent_name}", agent_name.upper(), "openclaw")
        self.agent_name = agent_name
        self.gateway_url = gateway_url
        self.token = token
        self.openclaw_ws: Optional[websockets.WebSocketClientProtocol] = None
        self._openclaw_task: Optional[asyncio.Task] = None
        self._gateway_reconnect_task: Optional[asyncio.Task] = None

    def get_capabilities(self) -> List[str]:
        capabilities = ["messaging", "tasks"]
        if self.agent_name in ["ceo", "cto", "cfo", "coo", "cmo"]:
            capabilities.extend(["management", "decision"])
        if self.agent_name in ["cto"]:
            capabilities.extend(["code", "deployment", "architecture"])
        if self.agent_name in ["cfo"]:
            capabilities.extend(["finance", "budgeting"])
        return capabilities

    async def connect_gateway(self) -> bool:
        """连接到OpenClaw网关"""
        try:
            self.openclaw_ws = await websockets.connect(
                self.gateway_url,
                ping_interval=30,
                ping_timeout=90,
                extra_headers={"Authorization": f"Bearer {self.token}"} if self.token else None
            )
            self._openclaw_task = asyncio.create_task(self._openclaw_receive_loop())
            self._gateway_reconnect_task = asyncio.create_task(self._gateway_reconnect_loop())
            logger.info(f"Connected to OpenClaw gateway: {self.gateway_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to OpenClaw gateway: {e}")
            return False

    async def disconnect_gateway(self):
        """断开OpenClaw网关连接"""
        if self._openclaw_task:
            self._openclaw_task.cancel()
        if self._gateway_reconnect_task:
            self._gateway_reconnect_task.cancel()
        if self.openclaw_ws:
            await self.openclaw_ws.close()
            self.openclaw_ws = None
        logger.info("Disconnected from OpenClaw gateway")

    async def _gateway_reconnect_loop(self):
        """OpenClaw网关重连循环"""
        while self.openclaw_ws:
            try:
                await asyncio.sleep(30)
                # 检查连接状态
                if self.openclaw_ws and self.openclaw_ws.close_code:
                    logger.warning("OpenClaw gateway connection lost")
                    break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Gateway reconnect check error: {e}")

    async def _openclaw_receive_loop(self):
        """接收OpenClaw消息"""
        try:
            async for message in self.openclaw_ws:
                try:
                    data = json.loads(message)
                    await self._handle_openclaw_message(data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid OpenClaw message: {message}")
        except websockets.exceptions.ConnectionClosed:
            logger.warning("OpenClaw gateway connection closed")
        except asyncio.CancelledError:
            pass

    async def _handle_openclaw_message(self, data: Dict[str, Any]):
        """处理OpenClaw消息"""
        msg_type = data.get("type")

        if msg_type == "message":
            await self.send_message(
                data.get("to", "hermes-brain"),
                data.get("payload", {})
            )
        elif msg_type == "task":
            await self.send_task(
                data.get("to", "hermes-brain"),
                data.get("title", ""),
                data.get("description", ""),
                data.get("priority", "normal")
            )

    async def on_message(self, message: Message):
        """处理来自Agent Mesh的消息"""
        if message.type == MessageType.MESSAGE:
            await self._send_to_openclaw({
                "type": "message",
                "from": message.from_agent,
                "to": self.agent_name,
                "payload": message.payload
            })
        elif message.type == MessageType.TASK:
            await self._send_to_openclaw({
                "type": "task",
                "from": message.from_agent,
                "to": self.agent_name,
                "payload": message.payload
            })
        elif message.type == MessageType.TASK_UPDATE:
            await self._send_to_openclaw({
                "type": "task_update",
                "payload": message.payload
            })

    async def _send_to_openclaw(self, data: Dict[str, Any]) -> bool:
        """发送消息到OpenClaw"""
        if not self.openclaw_ws:
            return False
        try:
            await self.openclaw_ws.send(json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Failed to send to OpenClaw: {e}")
            return False

    async def send_to_agent(self, target_agent: str, message: str) -> bool:
        """通过OpenClaw发送消息给其他Agent"""
        return await self._send_to_openclaw({
            "type": "message",
            "from": self.agent_name,
            "to": target_agent,
            "payload": {"text": message}
        })

    async def disconnect(self, reason: str = "manual"):
        """断开所有连接"""
        await self.disconnect_gateway()
        await super().disconnect(reason)


class OpenClawCEOAdapter(OpenClawAdapter):
    """OpenClaw CEO专用适配器"""

    def __init__(self, gateway_url: str = "ws://127.0.0.1:18790", token: str = ""):
        super().__init__("ceo", gateway_url, token)

    def get_capabilities(self) -> List[str]:
        return ["management", "decision", "coordination", "approval"]


class OpenClawCTOAdapter(OpenClawAdapter):
    """OpenClaw CTO专用适配器"""

    def __init__(self, gateway_url: str = "ws://127.0.0.1:18790", token: str = ""):
        super().__init__("cto", gateway_url, token)

    def get_capabilities(self) -> List[str]:
        return ["code", "deployment", "architecture", "technical-review"]
