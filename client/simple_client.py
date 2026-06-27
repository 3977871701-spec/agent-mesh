#!/usr/bin/env python3
"""
Agent Mesh 简单客户端 - 用于测试和演示
用法: python3 simple_client.py <agent_id> <agent_name>
"""
import asyncio
import json
import sys
from datetime import datetime

try:
    import websockets
except ImportError:
    print("需要安装 websockets: pip install websockets")
    sys.exit(1)


class AgentMeshClient:
    def __init__(self, agent_id: str, agent_name: str, agent_type: str = "custom"):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.ws = None
        self.running = True

    async def connect(self, url: str = "ws://localhost:18800"):
        """连接到Agent Mesh服务器"""
        print(f"连接到 {url}...")
        self.ws = await websockets.connect(url, ping_interval=30, ping_timeout=90)

        # 注册
        await self.ws.send(json.dumps({
            "type": "register",
            "payload": {
                "id": self.agent_id,
                "name": self.agent_name,
                "type": self.agent_type
            }
        }))
        print(f"已注册为 {self.agent_name} ({self.agent_id})")

    async def send_message(self, to: str, text: str):
        """发送消息"""
        await self.ws.send(json.dumps({
            "type": "message",
            "from": self.agent_id,
            "to": to,
            "payload": {"text": text},
            "timestamp": datetime.now().isoformat()
        }))
        print(f"发送给 {to}: {text}")

    async def listen(self):
        """监听消息"""
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

    async def handle_message(self, data: dict):
        """处理收到的消息"""
        msg_type = data.get("type")

        if msg_type == "register_response":
            print(f"注册响应: {data.get('payload', {}).get('message', 'OK')}")

        elif msg_type == "message":
            from_agent = data.get("from", "unknown")
            text = data.get("payload", {}).get("text", "")
            print(f"\n收到来自 {from_agent} 的消息: {text}")
            print(f"{self.agent_name}> ", end="", flush=True)

        elif msg_type == "heartbeat_ack":
            print(".", end="", flush=True)

        else:
            print(f"收到消息类型: {msg_type}")


async def main():
    if len(sys.argv) < 3:
        # 测试模式 - 启动一个测试agent
        agent_id = "test-" + datetime.now().strftime("%H%M%S")
        agent_name = "测试Agent"
    else:
        agent_id = sys.argv[1]
        agent_name = sys.argv[2]

    agent_type = sys.argv[3] if len(sys.argv) > 3 else "test"

    client = AgentMeshClient(agent_id, agent_name, agent_type)

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