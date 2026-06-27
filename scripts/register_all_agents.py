#!/usr/bin/env python3
"""注册所有Agent到Agent Mesh"""
import asyncio
import json
import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from server.database import Database
from server.models import Agent, AgentStatus


async def register_openclaw_agents(db: Database):
    """注册OpenClaw Agents"""
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    if not config_path.exists():
        print("⚠️  OpenClaw config not found")
        return

    with open(config_path) as f:
        config = json.load(f)

    agents = config.get("agents", {}).get("list", [])
    print(f"📌 Found {len(agents)} OpenClaw agents")

    for agent_info in agents:
        agent_id = agent_info.get("id", "")
        name = agent_info.get("name", agent_id) or agent_id

        agent = Agent(
            id=f"openclaw-{agent_id}",
            name=name.upper() if name else agent_id.upper(),
            type="openclaw",
            status=AgentStatus.OFFLINE,
            capabilities=["messaging", "tasks"],
            metadata={
                "source": "openclaw",
                "original_id": agent_id,
                "model": agent_info.get("model", {}).get("primary", "unknown")
            }
        )
        await db.add_agent(agent)
        print(f"  ✓ Registered: openclaw-{agent_id} ({name})")


async def register_hermes_agent(db: Database):
    """注册Hermes Agent"""
    hermes_path = Path.home() / ".hermes" / "config.yaml"
    if not hermes_path.exists():
        print("⚠️  Hermes config not found")
        return

    agent = Agent(
        id="hermes-brain",
        name="Hermes Brain",
        type="hermes",
        status=AgentStatus.OFFLINE,
        capabilities=["decision", "coordination", "verification", "brain"],
        metadata={"source": "hermes", "config_path": str(hermes_path)}
    )
    await db.add_agent(agent)
    print(f"  ✓ Registered: hermes-brain")


async def register_codex_agents(db: Database):
    """注册Codex Agents"""
    codex_path = Path.home() / ".codex"
    if not codex_path.exists():
        print("⚠️  Codex config not found")
        return

    # Codex typically has a main agent
    agent = Agent(
        id="codex-main",
        name="Codex",
        type="codex",
        status=AgentStatus.OFFLINE,
        capabilities=["code", "analysis", "generation"],
        metadata={"source": "codex"}
    )
    await db.add_agent(agent)
    print(f"  ✓ Registered: codex-main")


async def register_claude_agents(db: Database):
    """注册Claude Code Agents"""
    # Claude Code agents are typically registered in CLAUDE.md files
    claude_dir = Path.home()
    # Look for any project with CLAUDE.md
    agent = Agent(
        id="claude-code",
        name="Claude Code",
        type="claude",
        status=AgentStatus.OFFLINE,
        capabilities=["coding", "reasoning", "analysis", "creative"],
        metadata={"source": "claude"}
    )
    await db.add_agent(agent)
    print(f"  ✓ Registered: claude-code")


async def register_phoenix_agents(db: Database):
    """注册Phoenix (不死鸟) Agents"""
    phoenix_path = Path.home() / "Projects" / "不死鸟" / "phoenix-v5.1.1-release" / "phoenix-v5.1.1-release" / "config.json"
    if not phoenix_path.exists():
        print("⚠️  Phoenix config not found")
        return

    with open(phoenix_path) as f:
        config = json.load(f)

    # Phoenix has routing capabilities
    agent = Agent(
        id="phoenix-router",
        name="Phoenix Router",
        type="phoenix",
        status=AgentStatus.OFFLINE,
        capabilities=["routing", "cost-control", "model-selection", "load-balancing"],
        metadata={
            "source": "phoenix",
            "version": config.get("version", "5.1.1"),
            "daily_limit": config.get("executor", {}).get("budget", {}).get("daily_limit_usd", 3.3),
            "monthly_limit": config.get("executor", {}).get("budget", {}).get("monthly_limit_usd", 100)
        }
    )
    await db.add_agent(agent)
    print(f"  ✓ Registered: phoenix-router")


async def main():
    db = Database("./data/agent_mesh.db")
    await db.connect()

    print("🚀 Registering all agents to Agent Mesh...\n")

    await register_openclaw_agents(db)
    await register_hermes_agent(db)
    await register_codex_agents(db)
    await register_claude_agents(db)
    await register_phoenix_agents(db)

    # List all registered agents
    print("\n📊 All registered agents:")
    agents = await db.get_all_agents()
    for agent in agents:
        status_icon = "🟢" if agent.status == AgentStatus.ONLINE else "⚪"
        print(f"  {status_icon} {agent.id} [{agent.type}] - {agent.name}")

    print(f"\n✅ Total: {len(agents)} agents registered")

    await db.close()


if __name__ == "__main__":
    asyncio.run(main())