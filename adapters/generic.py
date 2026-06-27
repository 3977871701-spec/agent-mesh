"""通用适配器 - 用于自定义Agent"""
from typing import Dict, Any, List, Optional, Callable
from .base import BaseAdapter
from server.models import Message, MessageType


class GenericAdapter(BaseAdapter):
    """通用Agent适配器"""

    def __init__(
        self,
        agent_id: str,
        name: str,
        capabilities: List[str] = None,
        message_handler: Optional[Callable] = None
    ):
        super().__init__(agent_id, name, "custom")
        self._capabilities = capabilities or []
        self._message_handler = message_handler

    def get_capabilities(self) -> List[str]:
        return self._capabilities

    async def on_message(self, message: Message):
        """处理收到的消息"""
        if self._message_handler:
            await self._message_handler(message)
        else:
            # 默认处理：打印消息
            print(f"[{self.name}] Received from {message.from_agent}: {message.payload}")

    def set_message_handler(self, handler: Callable):
        """设置消息处理器"""
        self._message_handler = handler


class EchoAdapter(GenericAdapter):
    """回声适配器 - 用于测试"""

    def __init__(self, agent_id: str = "echo-agent"):
        super().__init__(agent_id, "Echo Agent", ["echo", "test"])

    async def on_message(self, message: Message):
        """回声消息"""
        if message.type == MessageType.MESSAGE:
            # 回复发送者
            await self.send_message(
                message.from_agent,
                {"text": f"Echo: {message.payload.get('text', '')}"}
            )
        elif message.type == MessageType.TASK:
            # 自动完成任务
            task_id = message.payload.get("task_id")
            if task_id:
                await self.update_task(task_id, "completed", {"result": "Task echoed"})


class LoggerAdapter(GenericAdapter):
    """日志适配器 - 记录所有消息"""

    def __init__(self, agent_id: str = "logger-agent", log_file: str = "agent_messages.log"):
        super().__init__(agent_id, "Logger Agent", ["logging"])
        self.log_file = log_file

    async def on_message(self, message: Message):
        """记录消息到文件"""
        log_entry = f"[{message.created_at}] {message.type.value}: {message.from_agent} -> {message.to_agent}: {message.payload}\n"
        with open(self.log_file, "a") as f:
            f.write(log_entry)
        print(f"[Logger] {log_entry.strip()}")
