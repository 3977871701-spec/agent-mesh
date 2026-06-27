"""OpenClaw Gateway Bridge - 连接OpenClaw Agent系统"""
import asyncio
import json
import logging
import uuid
from typing import Dict, Optional, Callable
import websockets

logger = logging.getLogger(__name__)


class OpenClawBridge:
    """OpenClaw Gateway桥接器 - 使用JSON-RPC协议"""

    def __init__(self, gateway_url: str = "ws://127.0.0.1:18790", token: str = ""):
        self.gateway_url = gateway_url
        self.token = token
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self._receive_task: Optional[asyncio.Task] = None
        self._message_handlers: Dict[str, Callable] = {}
        self._pending_requests: Dict[str, asyncio.Future] = {}

    async def connect(self) -> bool:
        """连接到OpenClaw Gateway - 实现challenge-response认证"""
        try:
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"

            self.ws = await websockets.connect(
                self.gateway_url,
                additional_headers=headers if headers else {},
                ping_interval=30,
                ping_timeout=90
            )
            logger.info(f"已连接到OpenClaw Gateway")

            # Step 1: 接收challenge
            challenge_msg = await asyncio.wait_for(self.ws.recv(), timeout=10)
            challenge_data = json.loads(challenge_msg)

            if challenge_data.get("type") == "event" and challenge_data.get("event") == "connect.challenge":
                nonce = challenge_data.get("payload", {}).get("nonce")

                # Step 2: 发送JSON-RPC connect请求
                connect_id = str(uuid.uuid4())
                connect_params = {
                    "minProtocol": 3,
                    "maxProtocol": 3,
                    "client": {
                        "id": "gateway-client",
                        "mode": "backend",
                        "platform": "darwin",
                        "version": "5.14.0"
                    },
                    "auth": {
                        "token": self.token
                    },
                    "role": "operator",
                    "scopes": ["operator.read", "operator.write", "operator.talk.secrets"]
                }

                req_msg = {
                    "type": "req",
                    "id": connect_id,
                    "method": "connect",
                    "params": connect_params
                }
                await self.ws.send(json.dumps(req_msg))
                logger.info("已发送connect请求")

                # Step 3: 等待认证结果
                auth_result = await asyncio.wait_for(self.ws.recv(), timeout=10)
                auth_data = json.loads(auth_result)

                if not auth_data.get("ok"):
                    error = auth_data.get("error", {})
                    logger.error(f"OpenClaw认证失败: {error.get('message', 'Unknown error')}")
                    await self.ws.close()
                    return False

                logger.info("OpenClaw认证成功!")

            self.connected = True
            self._receive_task = asyncio.create_task(self._receive_loop())
            logger.info(f"Connected to OpenClaw Gateway: {self.gateway_url}")
            return True

        except asyncio.TimeoutError:
            logger.error("等待消息超时")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to OpenClaw Gateway: {e}")
            return False

    async def disconnect(self):
        """断开连接"""
        self.connected = False
        if self._receive_task:
            self._receive_task.cancel()
        if self.ws:
            await self.ws.close()
        logger.info("Disconnected from OpenClaw Gateway")

    async def _receive_loop(self):
        """接收来自Gateway的消息"""
        try:
            async for msg in self.ws:
                try:
                    data = json.loads(msg)
                    await self._handle_message(data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from Gateway: {msg}")
        except websockets.exceptions.ConnectionClosed:
            logger.warning("OpenClaw Gateway connection closed")
            self.connected = False
            # 尝试重连
            await asyncio.sleep(5)
            await self.connect()
        except asyncio.CancelledError:
            pass

    async def _handle_message(self, data: Dict):
        """处理Gateway消息"""
        msg_type = data.get("type")
        event = data.get("event")

        # 处理session.message事件 (来自agents的消息)
        if msg_type == "event" and event == "session.message":
            payload = data.get("payload", {})
            message_data = payload.get("message", {})

            # 支持多种格式: text字段 或 content字段
            if isinstance(message_data, dict):
                text = message_data.get("text") or message_data.get("content", "")
                if isinstance(text, list):
                    text = text[0].get("text", "") if text else ""
                role = message_data.get("role", "")
            else:
                text = str(message_data) if message_data else ""
                role = ""

            logger.info(f"session.message event: from={payload.get('agentId')}, role={role}, text={str(text)[:50]}")

            handler = self._message_handlers.get("session.message")
            if handler:
                await handler({
                    "from": payload.get("agentId", "unknown"),
                    "text": text,
                    "role": role,
                    "source": "openclaw",
                    "session_key": payload.get("sessionKey", "")
                })
            return

        # 处理chat事件 (OpenClaw agent的回复)
        if msg_type == "event" and event == "chat":
            payload = data.get("payload", {})
            message_data = payload.get("message", {})

            if isinstance(message_data, dict):
                content = message_data.get("content", "")
                if isinstance(content, list):
                    content = content[0].get("text", "") if content else ""
                role = message_data.get("role", "")
            else:
                content = str(message_data) if message_data else ""
                role = ""

            # 只处理assistant的最终回复(state=final)，跳过中间过程
            state = payload.get("state", "")
            if role == "assistant" and content and state == "final":
                logger.info(f"chat event: role={role}, text={str(content)[:50]}")
                handler = self._message_handlers.get("session.message")
                if handler:
                    await handler({
                        "from": payload.get("sessionKey", "").split(":")[1] if payload.get("sessionKey") else "unknown",
                        "text": content,
                        "role": role,
                        "source": "openclaw",
                        "session_key": payload.get("sessionKey", "")
                    })
            return

        # 处理响应消息 (响应我们之前发送的请求)
        if msg_type == "res":
            req_id = data.get("id")
            logger.info(f"RES message received: id={req_id}, pending keys={list(self._pending_requests.keys())}")
            if req_id and req_id in self._pending_requests:
                future = self._pending_requests.pop(req_id)
                if not future.done():
                    future.set_result(data)
                logger.info(f"Resolved pending request: {req_id}")
            return

        # 转发其他消息给注册的处理器
        handler = self._message_handlers.get(msg_type)
        if handler:
            await handler(data)

    def register_handler(self, msg_type: str, handler: Callable):
        """注册消息处理器"""
        self._message_handlers[msg_type] = handler

    async def send_to_agent(self, agent_id: str, message: Dict, timeout: float = 60) -> Optional[Dict]:
        """发送消息给指定Agent - 使用sessions.send直接发送"""
        if not self.connected:
            logger.warning("Not connected to Gateway")
            return None

        try:
            text = message.get("text", "") if isinstance(message, dict) else str(message)

            # 先获取或创建会话
            session_key = await self._get_or_create_session(agent_id)
            if not session_key:
                logger.error(f"Failed to get session for {agent_id}")
                return None

            logger.info(f"Using session {session_key} for {agent_id}")

            # 直接发送消息
            req_id = str(uuid.uuid4())
            future = asyncio.Future()
            self._pending_requests[req_id] = future

            payload = {
                "type": "req",
                "id": req_id,
                "method": "sessions.send",
                "params": {
                    "key": session_key,
                    "message": text,
                    "idempotencyKey": req_id
                }
            }
            await self.ws.send(json.dumps(payload))
            logger.info(f"已发送消息到 {agent_id}: {text[:50]}...")

            # 等待响应
            try:
                response = await asyncio.wait_for(future, timeout=timeout)
                logger.info(f"收到响应 from {agent_id}")
                return response
            except asyncio.TimeoutError:
                logger.error(f"Timeout waiting for response from {agent_id}")
                self._pending_requests.pop(req_id, None)
                return None

        except Exception as e:
            logger.error(f"Failed to send to {agent_id}: {e}")
            return None

    async def _get_or_create_session(self, agent_id: str) -> Optional[str]:
        """获取或创建会话"""
        try:
            # 先尝试获取现有的会话
            req_id = str(uuid.uuid4())
            future = asyncio.Future()
            self._pending_requests[req_id] = future

            await self.ws.send(json.dumps({
                "type": "req",
                "id": req_id,
                "method": "sessions.list",
                "params": {
                    "agentId": agent_id
                }
            }))

            # 等待响应（最多10秒）
            try:
                response = await asyncio.wait_for(future, timeout=10)
            except asyncio.TimeoutError:
                logger.error(f"sessions.list timeout for {agent_id}")
                self._pending_requests.pop(req_id, None)
                return await self._create_session(agent_id)

            if response and response.get("ok"):
                sessions = response.get("payload", {}).get("sessions", [])
                if sessions:
                    return sessions[0].get("key")

            # 如果没有现有会话，创建一个新会话
            return await self._create_session(agent_id)

        except Exception as e:
            logger.error(f"Failed to get/create session for {agent_id}: {e}")
            return None

    async def _create_session(self, agent_id: str) -> Optional[str]:
        """创建新会话"""
        try:
            req_id = str(uuid.uuid4())
            future = asyncio.Future()
            self._pending_requests[req_id] = future

            await self.ws.send(json.dumps({
                "type": "req",
                "id": req_id,
                "method": "sessions.create",
                "params": {
                    "agentId": agent_id,
                    "label": "agent-mesh-bridge"
                }
            }))

            # 等待响应（最多10秒）
            try:
                response = await asyncio.wait_for(future, timeout=10)
            except asyncio.TimeoutError:
                logger.error(f"sessions.create timeout for {agent_id}")
                self._pending_requests.pop(req_id, None)
                return None

            if response and response.get("ok"):
                return response.get("payload", {}).get("key")
            else:
                error = response.get("error", {}) if response else {}
                logger.error(f"Session create failed: {error.get('message')}")
        except Exception as e:
            logger.error(f"Failed to create session for {agent_id}: {e}")

        return None

    async def send_and_wait(self, agent_id: str, message: Dict, timeout: float = 60) -> Optional[Dict]:
        """发送消息并等待响应"""
        return await self.send_to_agent(agent_id, message, timeout)

    async def list_agents(self) -> Optional[Dict]:
        """列出所有agents"""
        if not self.connected:
            return None

        try:
            req_id = str(uuid.uuid4())
            future = asyncio.Future()
            self._pending_requests[req_id] = future

            await self.ws.send(json.dumps({
                "type": "req",
                "id": req_id,
                "method": "agents.list",
                "params": {}
            }))

            response = await asyncio.wait_for(future, timeout=10)
            return response.get("payload")

        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            return None

    async def create_session(self, agent_id: str, system_prompt: str = "") -> Optional[str]:
        """为指定agent创建会话"""
        if not self.connected:
            return None

        try:
            req_id = str(uuid.uuid4())
            future = asyncio.Future()
            self._pending_requests[req_id] = future

            await self.ws.send(json.dumps({
                "type": "req",
                "id": req_id,
                "method": "sessions.create",
                "params": {
                    "agentId": agent_id,
                    "systemPrompt": system_prompt
                }
            }))

            response = await asyncio.wait_for(future, timeout=10)
            if response.get("ok"):
                return response.get("payload", {}).get("sessionKey")
        except Exception as e:
            logger.error(f"Failed to create session: {e}")

        return None

    def is_connected(self) -> bool:
        return self.connected

    def get_handlers(self) -> Dict[str, Callable]:
        return self._message_handlers.copy()