#!/usr/bin/env python3
"""
OpenClaw Agent Mesh Client - 直接连接到Agent Mesh的客户端
用法: python3 mesh_agent_client.py <agent_id> <openclaw_agent_name>
例如: python3 mesh_agent_client.py openclaw-ceo ceo
"""
import asyncio
import json
import sys
import uuid
from datetime import datetime

try:
    import websockets
except ImportError:
    print("需要安装 websockets: pip install websockets")
    sys.exit(1)


class MeshAgentClient:
    def __init__(self, mesh_id: str, openclaw_name: str, mesh_url: str = "ws://localhost:18800"):
        self.mesh_id = mesh_id
        self.openclaw_name = openclaw_name
        self.mesh_url = mesh_url
        self.ws = None
        self.running = True
        self.mesh_token = "1772ca43c48f4b2d9f2e8b7c6a1f0e9d3d34"
        self.pending_responses = {}

    async def connect(self):
        """连接到Agent Mesh"""
        print(f"连接到 Agent Mesh: {self.mesh_url}...")

        headers = {}
        if self.mesh_token:
            headers["Authorization"] = f"Bearer {self.mesh_token}"

        self.ws = await websockets.connect(
            self.mesh_url,
            additional_headers=headers if headers else {},
            ping_interval=30,
            ping_timeout=90
        )
        print(f"已连接!")

        # 注册为OpenClaw agent
        await self.ws.send(json.dumps({
            "type": "register",
            "payload": {
                "id": self.mesh_id,
                "name": f"OpenClaw-{self.openclaw_name.upper()}",
                "type": "openclaw",
                "capabilities": ["chat", "messaging"]
            }
        }))
        print(f"已注册为 {self.mesh_id}")

    async def listen(self):
        """监听来自Agent Mesh的消息"""
        print("开始监听消息... (按 Ctrl+C 退出)")
        try:
            async for msg in self.ws:
                try:
                    data = json.loads(msg)
                    await self.handle_message(data)
                except json.JSONDecodeError:
                    print(f"无效消息: {msg}")
        except websockets.exceptions.ConnectionClosed:
            print("连接已断开")
            self.running = False

    async def handle_message(self, data: dict):
        """处理收到的消息"""
        msg_type = data.get("type")

        if msg_type == "register_response":
            print(f"[系统] 注册成功!")

        elif msg_type == "message":
            from_agent = data.get("from", "unknown")
            text = data.get("payload", {}).get("text", "")
            print(f"\n[{from_agent}] {text}")
            print(f"{self.mesh_id}> ", end="", flush=True)

        elif msg_type == "ping":
            await self.ws.send(json.dumps({
                "type": "pong",
                "from": self.mesh_id
            }))

        elif msg_type == "shutdown":
            print("\n[系统] 收到关闭指令")
            self.running = False

        else:
            print(f"[收到] {msg_type}")


async def main():
    if len(sys.argv) < 3:
        print("用法: python3 mesh_agent_client.py <mesh_id> <openclaw_name>")
        print("例如: python3 mesh_agent_client.py openclaw-ceo ceo")
        sys.exit(1)

    mesh_id = sys.argv[1]
    openclaw_name = sys.argv[2]

    client = MeshAgentClient(mesh_id, openclaw_name)

    try:
        await client.connect()
        await client.listen()
    except KeyboardInterrupt:
        print("\n退出中...")
    finally:
        if client.ws:
            await client.ws.close()


if __name__ == "__main__":
    asyncio.run(main())
