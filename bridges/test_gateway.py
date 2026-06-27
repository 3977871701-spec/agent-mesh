#!/usr/bin/env python3
"""
OpenClaw Gateway 连接测试
"""
import asyncio
import json
import sys

try:
    import websockets
except ImportError:
    print("需要安装 websockets: pip install websockets")
    sys.exit(1)


async def test_gateway():
    url = "ws://127.0.0.1:18790"
    print(f"测试连接: {url}")

    # 尝试不带 token
    print("\n1. 尝试不带 token...")
    try:
        async with websockets.connect(url, ping_interval=30, ping_timeout=90) as ws:
            print("   连接成功！")
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            print(f"   收到消息: {msg}")

            # 发送注册
            await ws.send(json.dumps({
                "type": "register",
                "id": "test-bridge",
                "name": "Test Bridge",
                "capabilities": ["messaging"]
            }))
            print("   已发送注册请求")

            # 等待响应
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            print(f"   收到响应: {msg}")

    except Exception as e:
        print(f"   失败: {e}")

    # 尝试带 token
    print("\n2. 尝试带 token (Authorization header)...")
    try:
        async with websockets.connect(
            url,
            additional_headers={"Authorization": "Bearer 1772ca43c48f4b2d9f2e8b7c6a1f0e9d3d34"},
            ping_interval=30,
            ping_timeout=90
        ) as ws:
            print("   连接成功！")
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            print(f"   收到消息: {msg}")

    except Exception as e:
        print(f"   失败: {e}")

asyncio.run(test_gateway())