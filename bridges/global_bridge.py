#!/usr/bin/env python3
"""
Agent Mesh 全局桥接器
- 连接 OpenClaw Gateway (port 18790) - 支持 challenge-response 认证
- 连接 Agent Mesh WebSocket (port 18800)
- 转发两个系统之间的所有消息
"""
import asyncio
import json
import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import websockets
except ImportError:
    print("需要安装 websockets: pip install websockets")
    sys.exit(1)


class GlobalBridge:
    def __init__(
        self,
        openclaw_url: str = "ws://127.0.0.1:18790",
        mesh_url: str = "ws://127.0.0.1:18800",
        token: str = "1772ca43c48f4b2d9f2e8b7c6a1f0e9d3d34"  # OpenClaw gateway token
    ):
        self.openclaw_url = openclaw_url
        self.mesh_url = mesh_url
        self.token = token
        self.openclaw_ws = None
        self.mesh_ws = None
        self.running = False
        self.bridge_id = "global-bridge"
        self.bridge_name = "Global Bridge"

    async def start(self):
        """启动桥接器"""
        logger.info("=" * 50)
        logger.info("Agent Mesh 全局桥接器启动")
        logger.info("=" * 50)

        self.running = True

        # 同时连接两个系统
        mesh_task = asyncio.create_task(self._connect_mesh())
        oc_task = asyncio.create_task(self._connect_openclaw())

        # 等待任一连接失败
        done, pending = await asyncio.wait(
            [mesh_task, oc_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        for task in pending:
            task.cancel()

        self.running = False
        logger.info("桥接器已停止")

    async def _connect_mesh(self):
        """连接到 Agent Mesh"""
        logger.info(f"连接 Agent Mesh: {self.mesh_url}")

        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            async with websockets.connect(
                self.mesh_url,
                additional_headers=headers if headers else {},
                ping_interval=30,
                ping_timeout=90
            ) as ws:
                self.mesh_ws = ws
                logger.info("已连接到 Agent Mesh")

                # 注册为桥接代理
                await ws.send(json.dumps({
                    "type": "register",
                    "payload": {
                        "id": self.bridge_id,
                        "name": self.bridge_name,
                        "type": "bridge",
                        "capabilities": ["messaging", "forwarding", "routing"]
                    }
                }))
                logger.info(f"已注册为桥接代理: {self.bridge_id}")

                # 监听 Agent Mesh 的消息
                async for msg in ws:
                    try:
                        data = json.loads(msg)
                        await self._handle_mesh_message(data)
                    except json.JSONDecodeError:
                        logger.warning(f"无效消息: {msg}")

        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"Agent Mesh 连接断开: {e}")
        except Exception as e:
            logger.error(f"Agent Mesh 连接错误: {e}")

    async def _connect_openclaw(self):
        """连接到 OpenClaw Gateway"""
        logger.info(f"连接 OpenClaw Gateway: {self.openclaw_url}")

        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            async with websockets.connect(
                self.openclaw_url,
                additional_headers=headers if headers else {},
                ping_interval=30,
                ping_timeout=90
            ) as ws:
                self.openclaw_ws = ws
                logger.info("已连接到 OpenClaw Gateway")

                # Step 1: 接收 challenge
                challenge_msg = await asyncio.wait_for(ws.recv(), timeout=10)
                challenge_data = json.loads(challenge_msg)
                logger.info(f"收到 challenge")

                if challenge_data.get("type") == "event" and challenge_data.get("event") == "connect.challenge":
                    nonce = challenge_data.get("payload", {}).get("nonce")

                    # Step 2: 发送 JSON-RPC connect 请求
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
                    await ws.send(json.dumps(req_msg))
                    logger.info("已发送 connect 请求")

                    # Step 3: 等待认证结果
                    auth_result = await asyncio.wait_for(ws.recv(), timeout=10)
                    auth_data = json.loads(auth_result)
                    logger.info(f"认证结果: ok={auth_data.get('ok')}")

                    if not auth_data.get("ok"):
                        error = auth_data.get("error", {})
                        logger.error(f"OpenClaw 认证失败: {error.get('message', 'Unknown error')}")
                        return

                    logger.info("OpenClaw 认证成功!")

                # Step 4: 监听消息
                async for msg in ws:
                    try:
                        data = json.loads(msg)
                        await self._handle_openclaw_message(data)
                    except json.JSONDecodeError:
                        logger.warning(f"无效 OpenClaw 消息: {msg}")

        except asyncio.TimeoutError:
            logger.error("等待消息超时")
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"OpenClaw Gateway 连接断开: {e}")
        except Exception as e:
            logger.error(f"OpenClaw Gateway 连接错误: {e}")


    async def _handle_mesh_message(self, data: dict):
        """处理来自 Agent Mesh 的消息"""
        msg_type = data.get("type")

        if msg_type == "register_response":
            logger.info(f"Agent Mesh 注册响应: {data.get('payload', {}).get('message', 'OK')}")
            return

        # 转发消息到 OpenClaw
        if msg_type in ("message", "broadcast"):
            to_agent = data.get("to", "")
            from_agent = data.get("from", "console")
            payload = data.get("payload", {})

            # 提取原始文本
            text = payload.get("text", "") if isinstance(payload, dict) else str(payload)

            if msg_type == "message" and to_agent:
                # 点对点消息
                # 如果发给 openclaw-* 类型的 agent，转发到 OpenClaw
                if to_agent.startswith("openclaw-"):
                    original_id = to_agent.replace("openclaw-", "")
                    await self._forward_to_openclaw(original_id, from_agent, text, data)
                else:
                    # 广播消息
                    if to_agent in ("*", "all"):
                        await self._broadcast_to_openclaw(from_agent, text, data)

    async def _handle_openclaw_message(self, data: dict):
        """处理来自 OpenClaw Gateway 的消息"""
        msg_type = data.get("type")
        method = data.get("method")

        # 事件消息
        if msg_type == "event":
            event_name = data.get("event")
            payload = data.get("payload", {})

            if event_name == "session.message":
                from_agent = payload.get("agentId", "")
                text = payload.get("message", {}).get("text", "")
                if text:
                    await self._forward_to_mesh(f"openclaw-{from_agent}", "console", text, data)
            return

        # 响应消息
        if msg_type == "res":
            # 处理请求响应
            return

        # 主动发送的消息 (不是响应)
        if method == "send":
            from_agent = data.get("params", {}).get("agentId", "")
            text = data.get("params", {}).get("message", {}).get("text", "")
            if text:
                await self._forward_to_mesh(f"openclaw-{from_agent}", "console", text, data)

    async def _forward_to_openclaw(self, agent_id: str, from_id: str, text: str, original_data: dict):
        """转发消息到 OpenClaw (JSON-RPC send)"""
        if not self.openclaw_ws:
            logger.warning("OpenClaw 未连接，无法转发")
            return

        try:
            req_id = str(uuid.uuid4())
            await self.openclaw_ws.send(json.dumps({
                "type": "req",
                "id": req_id,
                "method": "send",
                "params": {
                    "agentId": agent_id,
                    "message": {"text": text}
                }
            }))
            logger.info(f"转发到 OpenClaw: {from_id} -> {agent_id}: {text[:50]}...")
        except Exception as e:
            logger.error(f"转发到 OpenClaw 失败: {e}")

    async def _broadcast_to_openclaw(self, from_id: str, text: str, original_data: dict):
        """广播消息到 OpenClaw (JSON-RPC)"""
        if not self.openclaw_ws:
            return

        try:
            req_id = str(uuid.uuid4())
            await self.openclaw_ws.send(json.dumps({
                "type": "req",
                "id": req_id,
                "method": "broadcast",
                "params": {
                    "message": {"text": text}
                }
            }))
            logger.info(f"广播到 OpenClaw: {from_id}: {text[:50]}...")
        except Exception as e:
            logger.error(f"广播到 OpenClaw 失败: {e}")

    async def _forward_to_mesh(self, from_id: str, to_id: str, text: str, original_data: dict):
        """转发消息到 Agent Mesh"""
        if not self.mesh_ws:
            logger.warning("Agent Mesh 未连接，无法转发")
            return

        try:
            await self.mesh_ws.send(json.dumps({
                "type": "message",
                "from": from_id,
                "to": to_id,
                "payload": {"text": text, "source": "openclaw"},
                "timestamp": datetime.now().isoformat()
            }))
            logger.info(f"转发到 Agent Mesh: {from_id} -> {to_id}: {text[:50]}...")
        except Exception as e:
            logger.error(f"转发到 Agent Mesh 失败: {e}")

    async def stop(self):
        """停止桥接器"""
        self.running = False
        if self.openclaw_ws:
            await self.openclaw_ws.close()
        if self.mesh_ws:
            await self.mesh_ws.close()


async def main():
    bridge = GlobalBridge()

    try:
        await bridge.start()
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在停止...")
        await bridge.stop()


if __name__ == "__main__":
    asyncio.run(main())