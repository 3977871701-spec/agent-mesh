#!/usr/bin/env python3
"""
OpenClaw Agent Mesh Runner
直接运行OpenClaw agent并连接到Agent Mesh进行通信

这个脚本会:
1. 连接到OpenClaw Gateway
2. 创建一个持久会话
3. 连接到Agent Mesh WebSocket
4. 作为该agent的代理,双向转发消息

用法: python3 mesh_agent_runner.py <mesh_id> <openclaw_agent_id>
例如: python3 mesh_agent_runner.py openclaw-ceo ceo
"""
import asyncio
import json
import sys
import uuid
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import websockets
except ImportError:
    print("需要安装 websockets: pip install websockets")
    sys.exit(1)


class MeshAgentRunner:
    def __init__(self, mesh_id: str, openclaw_id: str,
                 mesh_url: str = "ws://localhost:18800",
                 gateway_url: str = "ws://localhost:18790",
                 mesh_token: str = "1772ca43c48f4b2d9f2e8b7c6a1f0e9d3d34",
                 gateway_token: str = "1772ca43c48f4b2d9f2e8b7c6a1f0e9d3d34"):
        self.mesh_id = mesh_id
        self.openclaw_id = openclaw_id
        self.mesh_url = mesh_url
        self.gateway_url = gateway_url
        self.mesh_token = mesh_token
        self.gateway_token = gateway_token

        self.mesh_ws = None
        self.gateway_ws = None
        self.session_key = None
        self.running = True
        self.pending_requests = {}

    async def start(self):
        """启动runner"""
        logger.info(f"启动 MeshAgentRunner: mesh_id={self.mesh_id}, openclaw_id={self.openclaw_id}")

        # 启动mesh和gateway连接
        mesh_task = asyncio.create_task(self._connect_mesh())
        gateway_task = asyncio.create_task(self._connect_gateway())

        # 等待任一连接失败
        done, pending = await asyncio.wait(
            [mesh_task, gateway_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        for task in pending:
            task.cancel()

        logger.info("Runner已停止")

    async def _connect_gateway(self):
        """连接到OpenClaw Gateway并创建会话"""
        logger.info(f"连接到 OpenClaw Gateway: {self.gateway_url}")

        try:
            headers = {}
            if self.gateway_token:
                headers["Authorization"] = f"Bearer {self.gateway_token}"

            async with websockets.connect(
                self.gateway_url,
                additional_headers=headers,
                ping_interval=30,
                ping_timeout=90
            ) as ws:
                self.gateway_ws = ws
                logger.info("已连接到 OpenClaw Gateway")

                # 处理challenge-response认证
                challenge = await asyncio.wait_for(ws.recv(), timeout=10)
                challenge_data = json.loads(challenge)

                if challenge_data.get("type") == "event" and challenge_data.get("event") == "connect.challenge":
                    nonce = challenge_data["payload"]["nonce"]

                    req_id = str(uuid.uuid4())
                    connect_req = {
                        "type": "req",
                        "id": req_id,
                        "method": "connect",
                        "params": {
                            "minProtocol": 3,
                            "maxProtocol": 3,
                            "client": {
                                "id": "gateway-client",
                                "mode": "backend",
                                "platform": "darwin",
                                "version": "1.0.0"
                            },
                            "auth": {"token": self.gateway_token},
                            "role": "operator",
                            "scopes": ["operator.read", "operator.write", "operator.talk.secrets"]
                        }
                    }
                    await ws.send(json.dumps(connect_req))

                    resp = await asyncio.wait_for(ws.recv(), timeout=10)
                    resp_data = json.loads(resp)
                    if not resp_data.get("ok"):
                        logger.error(f"Gateway认证失败: {resp_data.get('error')}")
                        return

                    logger.info("Gateway认证成功!")

                # 创建持久会话
                await self._create_session()

                # 监听来自gateway的消息
                async for msg in ws:
                    try:
                        data = json.loads(msg)
                        await self._handle_gateway_message(data)
                    except json.JSONDecodeError:
                        logger.warning(f"无效消息: {msg}")

        except Exception as e:
            logger.error(f"Gateway连接错误: {e}")

    async def _create_session(self):
        """创建OpenClaw会话"""
        if not self.gateway_ws:
            return

        req_id = str(uuid.uuid4())
        future = asyncio.Future()
        self.pending_requests[req_id] = future

        req = {
            "type": "req",
            "id": req_id,
            "method": "sessions.create",
            "params": {
                "agentId": self.openclaw_id,
                "label": f"mesh-{self.mesh_id}"
            }
        }
        await self.gateway_ws.send(json.dumps(req))
        logger.info(f"创建会话 for {self.openclaw_id}...")

        try:
            resp = await asyncio.wait_for(future, timeout=10)
            if resp.get("ok"):
                self.session_key = resp.get("payload", {}).get("key")
                logger.info(f"会话创建成功: {self.session_key}")
            else:
                logger.error(f"会话创建失败: {resp.get('error')}")
        except asyncio.TimeoutError:
            logger.error("会话创建超时")
            self.pending_requests.pop(req_id, None)

    async def _handle_gateway_message(self, data: dict):
        """处理来自Gateway的消息"""
        msg_type = data.get("type")

        # 响应消息 - 解析pending请求
        if msg_type == "res":
            req_id = data.get("id")
            if req_id and req_id in self.pending_requests:
                future = self.pending_requests.pop(req_id)
                if not future.done():
                    future.set_result(data)
            return

        # 会话消息 - 来自agent的回复
        if msg_type == "event" and data.get("event") == "session.message":
            payload = data.get("payload", {})
            message_data = payload.get("message", {})
            text = message_data.get("text", "") if isinstance(message_data, dict) else message_data

            if text:
                logger.info(f"收到Agent回复: {text[:50]}...")
                # 转发到Agent Mesh
                await self._forward_to_mesh(text)

            # 同时检查是否有delivered响应
            reply = payload.get("reply", "")
            if reply:
                logger.info(f"收到Agent回复(delivered): {reply[:50]}...")
                await self._forward_to_mesh(reply)

    async def _forward_to_mesh(self, text: str):
        """转发消息到Agent Mesh"""
        if not self.mesh_ws:
            return

        try:
            msg = {
                "type": "message",
                "from": self.mesh_id,
                "to": "console",
                "payload": {"text": text, "source": "openclaw"},
                "timestamp": datetime.now().isoformat()
            }
            await self.mesh_ws.send(json.dumps(msg))
            logger.info(f"已转发到Mesh: {text[:50]}...")
        except Exception as e:
            logger.error(f"转发到Mesh失败: {e}")

    async def _connect_mesh(self):
        """连接到Agent Mesh"""
        logger.info(f"连接到 Agent Mesh: {self.mesh_url}")

        headers = {}
        if self.mesh_token:
            headers["Authorization"] = f"Bearer {self.mesh_token}"

        try:
            async with websockets.connect(
                self.mesh_url,
                additional_headers=headers,
                ping_interval=30,
                ping_timeout=90
            ) as ws:
                self.mesh_ws = ws
                logger.info("已连接到 Agent Mesh")

                # 注册为agent
                await ws.send(json.dumps({
                    "type": "register",
                    "payload": {
                        "id": self.mesh_id,
                        "name": f"OpenClaw-{self.openclaw_id.upper()}",
                        "type": "openclaw",
                        "capabilities": ["messaging", "chat"]
                    }
                }))
                logger.info(f"已在Mesh注册: {self.mesh_id}")

                # 等待session创建
                while not self.session_key and self.running:
                    await asyncio.sleep(0.1)

                # 监听来自mesh的消息
                async for msg in ws:
                    try:
                        data = json.loads(msg)
                        await self._handle_mesh_message(data)
                    except json.JSONDecodeError:
                        logger.warning(f"无效消息: {msg}")

        except Exception as e:
            logger.error(f"Mesh连接错误: {e}")

    async def _handle_mesh_message(self, data: dict):
        """处理来自Agent Mesh的消息"""
        msg_type = data.get("type")

        if msg_type == "register_response":
            logger.info(f"Mesh注册响应: {data.get('payload', {}).get('message', 'OK')}")
            return

        # 消息 - 转发到OpenClaw Gateway
        if msg_type in ("message", "broadcast"):
            text = data.get("payload", {}).get("text", "")
            from_agent = data.get("from", "console")

            if text:
                await self._send_to_gateway(text, from_agent)

    async def _send_to_gateway(self, text: str, from_id: str):
        """发送消息到OpenClaw Gateway"""
        if not self.gateway_ws or not self.session_key:
            logger.warning("Gateway未连接或无会话")
            return

        try:
            req_id = str(uuid.uuid4())
            req = {
                "type": "req",
                "id": req_id,
                "method": "sessions.send",
                "params": {
                    "key": self.session_key,
                    "message": text
                }
            }
            await self.gateway_ws.send(json.dumps(req))
            logger.info(f"发送到Gateway: {text[:50]}...")

        except Exception as e:
            logger.error(f"发送失败: {e}")


async def main():
    if len(sys.argv) < 3:
        print("用法: python3 mesh_agent_runner.py <mesh_id> <openclaw_agent_id>")
        print("例如: python3 mesh_agent_runner.py openclaw-ceo ceo")
        sys.exit(1)

    mesh_id = sys.argv[1]
    openclaw_id = sys.argv[2]

    runner = MeshAgentRunner(mesh_id, openclaw_id)

    try:
        await runner.start()
    except KeyboardInterrupt:
        logger.info("收到中断信号...")
        runner.running = False


if __name__ == "__main__":
    asyncio.run(main())
