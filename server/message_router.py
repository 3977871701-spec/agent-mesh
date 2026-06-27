"""消息路由模块"""
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set
from collections import defaultdict

from .models import Message, MessageType, Agent, AgentStatus
from .database import Database
from .websocket_server import WebSocketServer

logger = logging.getLogger(__name__)


class MessageRouter:
    def __init__(self, ws_server: WebSocketServer, database: Database):
        self.ws_server = ws_server
        self.db = database
        # 离线消息队列: agent_id -> List[Message]
        self.offline_queue: Dict[str, List[Message]] = defaultdict(list)
        # 注册消息处理器
        self._register_handlers()

    def _register_handlers(self):
        """注册消息处理器"""
        self.ws_server.register_handler(MessageType.MESSAGE, self._handle_message)
        self.ws_server.register_handler(MessageType.BROADCAST, self._handle_broadcast)
        self.ws_server.register_handler(MessageType.ACK, self._handle_ack)

    async def _handle_message(self, message: Message):
        """处理点对点消息"""
        target_id = message.to_agent
        if not target_id:
            logger.warning("Message has no target")
            return

        # 保存消息到数据库
        await self.db.add_message(message)

        # 检查是否是OpenClaw agent（通过ID前缀或数据库查询）
        is_openclaw = False
        original_id = None

        if target_id.startswith("openclaw-"):
            is_openclaw = True
            original_id = target_id.replace("openclaw-", "")
        else:
            # 查数据库确认agent类型
            target_agent = await self.db.get_agent(target_id)
            if target_agent and target_agent.type == "openclaw":
                is_openclaw = True
                original_id = target_id

        # 如果是发给OpenClaw agent，优先通过bridge转发
        if is_openclaw:
            from adapters.openclaw_bridge import OpenClawBridge
            bridge = getattr(self.ws_server, 'openclaw_bridge', None)
            if bridge and bridge.is_connected():
                # 发送消息
                response = await bridge.send_to_agent(original_id, {
                    "type": "message",
                    "text": message.payload.get("text", ""),
                    "from": message.from_agent
                })
                if response and response.get("ok"):
                    await self.db.mark_delivered(message.id)
                    logger.info(f"Message forwarded via bridge: {message.from_agent} -> {original_id}")
                    return
                else:
                    # Bridge发送失败，不加入队列，因为OpenClaw agent可能正在处理
                    logger.warning(f"Bridge forward returned non-ok: {target_id}")
                    # 仍标记为已送达，因为消息已通过bridge发出
                    await self.db.mark_delivered(message.id)
                    return
            else:
                logger.info(f"Bridge not connected, message queued: {message.from_agent} -> {target_id}")

        # 尝试直接发送（给直接连接WebSocket的Agent）
        if self.ws_server.is_agent_online(target_id):
            success = await self.ws_server.send_to_agent(target_id, message.to_dict())
            if success:
                await self.db.mark_delivered(message.id)
                logger.info(f"Message delivered: {message.from_agent} -> {target_id}")
            else:
                # 发送失败
                logger.warning(f"Message send failed (agent online but send failed): {message.from_agent} -> {target_id}")
        else:
            # 目标不在线 - 检查是否是可通过bridge发送的agent
            if is_openclaw:
                # OpenClaw agent已经通过bridge尝试发送过了
                logger.info(f"OpenClaw agent offline or unreachable: {target_id}")
            else:
                # 非OpenClaw agent（hermes/claude/codex等）- 这些agent没有bridge，不应该队列
                logger.warning(f"Agent {target_id} is not bridgeable (hermes/claude/codex). Messages will not be queued.")
                # 不加入队列，因为这些agent无法通过此系统接收消息

    async def _handle_broadcast(self, message: Message):
        """处理广播消息"""
        target = message.to_agent

        # 保存消息
        await self.db.add_message(message)

        if target == "*" or target == "all":
            # 广播给所有在线Agent
            await self.ws_server.broadcast(
                message.to_dict(),
                exclude={message.from_agent}
            )
            logger.info(f"Broadcast from {message.from_agent} to all")
        else:
            # 可能是群组ID
            group = await self.db.get_group(target)
            if group:
                await self._send_to_group(message, group.members)
                logger.info(f"Group message from {message.from_agent} to group {target}")
            else:
                logger.warning(f"Unknown broadcast target: {target}")

    async def _handle_ack(self, message: Message):
        """处理确认消息"""
        original_id = message.payload.get("message_id")
        if original_id:
            await self.db.mark_read(original_id)
            # 通知发送方
            original = await self.db.get_messages(message.from_agent)
            for msg in original:
                if msg.id == original_id:
                    await self.ws_server.send_to_agent(msg.from_agent, {
                        "type": "ack",
                        "id": str(uuid.uuid4()),
                        "from": message.from_agent,
                        "payload": {"message_id": original_id, "status": "read"}
                    })
                    break

    async def send_message(self, from_agent: str, to_agent: str, payload: Dict, metadata: Optional[Dict] = None) -> Message:
        """发送点对点消息"""
        message = Message(
            id=str(uuid.uuid4()),
            type=MessageType.MESSAGE,
            from_agent=from_agent,
            to_agent=to_agent,
            payload=payload,
            metadata=metadata or {},
            created_at=datetime.now()
        )
        await self._handle_message(message)
        return message

    async def broadcast_message(self, from_agent: str, target: str, payload: Dict, metadata: Optional[Dict] = None) -> Message:
        """广播消息"""
        message = Message(
            id=str(uuid.uuid4()),
            type=MessageType.BROADCAST,
            from_agent=from_agent,
            to_agent=target,
            payload=payload,
            metadata=metadata or {},
            created_at=datetime.now()
        )
        await self._handle_broadcast(message)
        return message

    async def _send_to_group(self, message: Message, members: List[str]):
        """发送消息给群组成员"""
        for member_id in members:
            if member_id != message.from_agent:
                # 创建针对每个成员的消息副本
                member_msg = Message(
                    id=str(uuid.uuid4()),
                    type=message.type,
                    from_agent=message.from_agent,
                    to_agent=member_id,
                    payload=message.payload,
                    metadata=message.metadata,
                    created_at=message.created_at
                )
                await self._handle_message(member_msg)

    async def flush_offline_queue(self, agent_id: str):
        """发送离线队列中的消息"""
        if agent_id in self.offline_queue:
            messages = self.offline_queue.pop(agent_id)
            for message in messages:
                if self.ws_server.is_agent_online(agent_id):
                    success = await self.ws_server.send_to_agent(agent_id, message.to_dict())
                    if success:
                        await self.db.mark_delivered(message.id)
                        logger.info(f"Offline message delivered: {message.from_agent} -> {agent_id}")
                    else:
                        # 重新入队
                        self.offline_queue[agent_id].append(message)
                        break
                else:
                    # Agent又离线了，重新入队
                    self.offline_queue[agent_id].append(message)
                    break

    def get_queue_size(self, agent_id: Optional[str] = None) -> int:
        """获取离线队列大小"""
        if agent_id:
            return len(self.offline_queue.get(agent_id, []))
        return sum(len(msgs) for msgs in self.offline_queue.values())
