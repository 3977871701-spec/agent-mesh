"""Hermes适配器 - 集成Hermes AI Agent系统"""
import asyncio
import json
import logging
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml

from .base import BaseAdapter
from server.models import Message, MessageType

logger = logging.getLogger(__name__)


class HermesAdapter(BaseAdapter):
    """Hermes AI Agent适配器"""

    def __init__(
        self,
        config_path: str = "~/.hermes/config.yaml",
        cli_path: str = "~/.hermes/cli"
    ):
        super().__init__("hermes-brain", "Hermes Brain", "hermes")
        self.config_path = Path(config_path).expanduser()
        self.cli_path = Path(cli_path).expanduser()
        self.config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """加载Hermes配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    self.config = yaml.safe_load(f) or {}
                logger.info(f"Loaded Hermes config from {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to load Hermes config: {e}")

    def get_capabilities(self) -> List[str]:
        return [
            "decision",
            "coordination",
            "verification",
            "brain",
            "task-management"
        ]

    async def on_message(self, message: Message):
        """处理收到的消息"""
        if message.type == MessageType.MESSAGE:
            response = await self._process_with_hermes(message.payload)
            if response:
                await self.send_message(message.from_agent, response)
        elif message.type == MessageType.TASK:
            await self._delegate_task(message)

    async def _process_with_hermes(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """通过Hermes CLI处理消息"""
        if not self.cli_path.exists():
            logger.warning(f"Hermes CLI not found: {self.cli_path}")
            return {"error": "Hermes CLI not available"}

        try:
            text = payload.get("text", "")
            cmd = f"{self.cli_path} process --input '{text}'"

            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return {"text": stdout.decode().strip()}
            else:
                logger.error(f"Hermes CLI error: {stderr.decode()}")
                return {"error": stderr.decode().strip()}
        except Exception as e:
            logger.error(f"Failed to process with Hermes: {e}")
            return {"error": str(e)}

    async def _delegate_task(self, message: Message):
        """将任务委托给CEO"""
        task_payload = message.payload
        task_id = task_payload.get("task_id")

        try:
            cmd = (
                f"/Users/xylei/.local/bin/openclaw-node24 agent "
                f"--agent ceo --channel webchat "
                f"--message '{json.dumps(task_payload)}'"
            )

            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                result = stdout.decode().strip()
                if task_id:
                    await self.update_task(task_id, "completed", {"result": result})
                logger.info(f"Task {task_id} delegated and completed")
            else:
                error = stderr.decode()
                logger.error(f"Task delegation failed: {error}")
                if task_id:
                    await self.update_task(task_id, "failed", {"error": error})
        except Exception as e:
            logger.error(f"Failed to delegate task: {e}")
            if task_id:
                await self.update_task(task_id, "failed", {"error": str(e)})

    async def send_to_ceo(self, message: str) -> bool:
        """直接发送消息给CEO"""
        return await self.send_message("openclaw-ceo", {"text": message})

    async def send_to_brain(self, message: str) -> bool:
        """发送消息给自己（Hermes大脑）"""
        response = await self._process_with_hermes({"text": message})
        return response is not None and "error" not in response

    def get_hermes_status(self) -> Dict[str, Any]:
        """获取Hermes状态"""
        return {
            "config_loaded": bool(self.config),
            "cli_available": self.cli_path.exists(),
            "config_path": str(self.config_path)
        }
