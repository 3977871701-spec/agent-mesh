"""Agent注册与发现模块"""
import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
import yaml

from .models import Agent, AgentStatus
from .database import Database
from .config import DiscoveryConfig

logger = logging.getLogger(__name__)


class AgentRegistry:
    def __init__(self, database: Database, config: DiscoveryConfig):
        self.db = database
        self.config = config
        # 已发现但未确认的Agent
        self.pending_agents: Dict[str, Agent] = {}
        # 已确认的Agent
        self.confirmed_agents: Set[str] = set()

    async def initialize(self):
        """初始化注册中心"""
        # 加载已确认的Agent
        agents = await self.db.get_all_agents()
        for agent in agents:
            self.confirmed_agents.add(agent.id)
        logger.info(f"Loaded {len(agents)} confirmed agents")

        # 自动发现
        if self.config.auto_discover:
            await self.discover_agents()

    async def discover_agents(self) -> List[Agent]:
        """扫描目录发现Agent"""
        discovered = []

        for scan_path in self.config.scan_paths:
            path = Path(scan_path).expanduser()
            if not path.exists():
                continue

            logger.info(f"Scanning {path} for agents...")

            # 根据路径类型处理
            if ".openclaw" in str(path):
                discovered.extend(await self._discover_openclaw_agents(path))
            elif ".hermes" in str(path):
                discovered.extend(await self._discover_hermes_agents(path))
            elif ".codex" in str(path):
                discovered.extend(await self._discover_codex_agents(path))

        logger.info(f"Discovered {len(discovered)} new agents")
        return discovered

    async def _discover_openclaw_agents(self, path: Path) -> List[Agent]:
        """发现OpenClaw Agent"""
        agents = []
        agents_dir = path / "agents"

        if not agents_dir.exists():
            return agents

        for agent_dir in agents_dir.iterdir():
            if agent_dir.is_dir() and not agent_dir.name.startswith("."):
                agent_id = f"openclaw-{agent_dir.name}"

                # 检查是否已确认
                if agent_id in self.confirmed_agents:
                    continue

                # 读取Agent配置
                config_file = agent_dir / "agent.json"
                metadata = {}
                if config_file.exists():
                    try:
                        with open(config_file, 'r') as f:
                            metadata = json.load(f)
                    except Exception:
                        pass

                agent = Agent(
                    id=agent_id,
                    name=agent_dir.name.upper(),
                    type="openclaw",
                    status=AgentStatus.OFFLINE,
                    capabilities=metadata.get("capabilities", []),
                    metadata=metadata
                )

                self.pending_agents[agent_id] = agent
                agents.append(agent)
                logger.info(f"Discovered OpenClaw agent: {agent_id}")

        return agents

    async def _discover_hermes_agents(self, path: Path) -> List[Agent]:
        """发现Hermes Agent"""
        agents = []
        config_file = path / "config.yaml"

        if not config_file.exists():
            return agents

        agent_id = "hermes-brain"

        # 检查是否已确认
        if agent_id in self.confirmed_agents:
            return agents

        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f) or {}

            agent = Agent(
                id=agent_id,
                name="Hermes Brain",
                type="hermes",
                status=AgentStatus.OFFLINE,
                capabilities=["decision", "coordination", "verification"],
                metadata={"config_path": str(config_file)}
            )

            self.pending_agents[agent_id] = agent
            agents.append(agent)
            logger.info(f"Discovered Hermes agent: {agent_id}")
        except Exception as e:
            logger.error(f"Error reading Hermes config: {e}")

        return agents

    async def _discover_codex_agents(self, path: Path) -> List[Agent]:
        """发现Codex Agent"""
        agents = []
        agent_id = "codex-main"

        # 检查是否已确认
        if agent_id in self.confirmed_agents:
            return agents

        if path.exists():
            agent = Agent(
                id=agent_id,
                name="Codex",
                type="codex",
                status=AgentStatus.OFFLINE,
                capabilities=["code", "analysis", "generation"],
                metadata={"config_path": str(path)}
            )

            self.pending_agents[agent_id] = agent
            agents.append(agent)
            logger.info(f"Discovered Codex agent: {agent_id}")

        return agents

    async def confirm_agent(self, agent_id: str) -> Optional[Agent]:
        """确认Agent加入系统"""
        if agent_id not in self.pending_agents:
            logger.warning(f"Agent {agent_id} not found in pending list")
            return None

        agent = self.pending_agents.pop(agent_id)

        # 保存到数据库
        await self.db.add_agent(agent)

        # 添加到已确认列表
        self.confirmed_agents.add(agent_id)

        logger.info(f"Agent confirmed: {agent_id}")
        return agent

    async def reject_agent(self, agent_id: str) -> bool:
        """拒绝Agent"""
        if agent_id in self.pending_agents:
            del self.pending_agents[agent_id]
            logger.info(f"Agent rejected: {agent_id}")
            return True
        return False

    async def register_agent(
        self,
        agent_id: Optional[str] = None,
        name: str = "",
        agent_type: str = "custom",
        capabilities: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> Agent:
        """手动注册新Agent"""
        if not agent_id:
            agent_id = f"{agent_type}-{str(uuid.uuid4())[:8]}"

        agent = Agent(
            id=agent_id,
            name=name or agent_id,
            type=agent_type,
            status=AgentStatus.OFFLINE,
            capabilities=capabilities or [],
            metadata=metadata or {},
            created_at=datetime.now()
        )

        await self.db.add_agent(agent)
        self.confirmed_agents.add(agent_id)

        logger.info(f"Agent registered: {agent_id}")
        return agent

    async def unregister_agent(self, agent_id: str) -> bool:
        """注销Agent"""
        if agent_id in self.confirmed_agents:
            self.confirmed_agents.remove(agent_id)
        await self.db.remove_agent(agent_id)
        logger.info(f"Agent unregistered: {agent_id}")
        return True

    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """获取Agent信息"""
        return await self.db.get_agent(agent_id)

    async def get_all_agents(self) -> List[Agent]:
        """获取所有已确认的Agent"""
        return await self.db.get_all_agents()

    async def get_online_agents(self) -> List[Agent]:
        """获取所有在线Agent"""
        agents = await self.db.get_all_agents()
        return [a for a in agents if a.status == AgentStatus.ONLINE]

    async def get_pending_agents(self) -> List[Agent]:
        """获取待确认的Agent"""
        return list(self.pending_agents.values())

    async def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """更新Agent状态"""
        return await self.db.update_agent_status(agent_id, status)

    async def get_agents_by_type(self, agent_type: str) -> List[Agent]:
        """按类型获取Agent"""
        agents = await self.db.get_all_agents()
        return [a for a in agents if a.type == agent_type]

    async def get_agents_by_capability(self, capability: str) -> List[Agent]:
        """按能力获取Agent"""
        agents = await self.db.get_all_agents()
        return [a for a in agents if capability in a.capabilities]

    def get_registry_stats(self) -> Dict[str, Any]:
        """获取注册中心统计信息"""
        return {
            "confirmed_count": len(self.confirmed_agents),
            "pending_count": len(self.pending_agents),
            "confirmed_agents": list(self.confirmed_agents),
            "pending_agents": list(self.pending_agents.keys())
        }
