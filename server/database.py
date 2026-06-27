"""数据库操作模块"""
import aiosqlite
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from .models import Agent, Message, Task, Group, AgentStatus, MessageType, TaskStatus, Priority


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db: Optional[aiosqlite.Connection] = None

    async def connect(self):
        """连接数据库"""
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        await self._create_tables()

    async def close(self):
        """关闭数据库连接"""
        if self.db:
            await self.db.close()

    async def _create_tables(self):
        """创建数据库表"""
        await self.db.executescript("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT,
                status TEXT DEFAULT 'offline',
                capabilities TEXT DEFAULT '[]',
                endpoint TEXT,
                metadata TEXT DEFAULT '{}',
                last_seen DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                type TEXT,
                from_agent TEXT,
                to_agent TEXT,
                payload TEXT DEFAULT '{}',
                metadata TEXT DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                delivered_at DATETIME,
                read_at DATETIME,
                FOREIGN KEY (from_agent) REFERENCES agents(id),
                FOREIGN KEY (to_agent) REFERENCES agents(id)
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                from_agent TEXT,
                to_agent TEXT,
                status TEXT DEFAULT 'pending',
                priority TEXT DEFAULT 'normal',
                result TEXT,
                deadline DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                FOREIGN KEY (from_agent) REFERENCES agents(id),
                FOREIGN KEY (to_agent) REFERENCES agents(id)
            );

            CREATE TABLE IF NOT EXISTS groups (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS group_members (
                group_id TEXT,
                agent_id TEXT,
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (group_id, agent_id),
                FOREIGN KEY (group_id) REFERENCES groups(id),
                FOREIGN KEY (agent_id) REFERENCES agents(id)
            );

            CREATE INDEX IF NOT EXISTS idx_messages_from ON messages(from_agent);
            CREATE INDEX IF NOT EXISTS idx_messages_to ON messages(to_agent);
            CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);
            CREATE INDEX IF NOT EXISTS idx_tasks_to ON tasks(to_agent);
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
        """)
        await self.db.commit()

    # ============ Agent 操作 ============

    async def add_agent(self, agent: Agent) -> bool:
        """添加Agent"""
        try:
            await self.db.execute(
                """INSERT OR REPLACE INTO agents
                   (id, name, type, status, capabilities, endpoint, metadata, last_seen, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (agent.id, agent.name, agent.type, agent.status.value,
                 json.dumps(agent.capabilities), agent.endpoint,
                 json.dumps(agent.metadata),
                 agent.last_seen.isoformat() if agent.last_seen else None,
                 agent.created_at.isoformat())
            )
            await self.db.commit()
            return True
        except Exception as e:
            print(f"Error adding agent: {e}")
            return False

    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """获取Agent"""
        async with self.db.execute(
            "SELECT * FROM agents WHERE id = ?", (agent_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return Agent(
                    id=row["id"],
                    name=row["name"],
                    type=row["type"],
                    status=AgentStatus(row["status"]),
                    capabilities=json.loads(row["capabilities"]) if row["capabilities"] else [],
                    endpoint=row["endpoint"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    last_seen=datetime.fromisoformat(row["last_seen"]) if row["last_seen"] else None,
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now()
                )
        return None

    async def get_all_agents(self) -> List[Agent]:
        """获取所有Agent"""
        agents = []
        async with self.db.execute("SELECT * FROM agents ORDER BY name") as cursor:
            async for row in cursor:
                agents.append(Agent(
                    id=row["id"],
                    name=row["name"],
                    type=row["type"],
                    status=AgentStatus(row["status"]),
                    capabilities=json.loads(row["capabilities"]) if row["capabilities"] else [],
                    endpoint=row["endpoint"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    last_seen=datetime.fromisoformat(row["last_seen"]) if row["last_seen"] else None,
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now()
                ))
        return agents

    async def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """更新Agent状态"""
        await self.db.execute(
            "UPDATE agents SET status = ?, last_seen = ? WHERE id = ?",
            (status.value, datetime.now().isoformat(), agent_id)
        )
        await self.db.commit()
        return True

    async def remove_agent(self, agent_id: str) -> bool:
        """删除Agent"""
        await self.db.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
        await self.db.commit()
        return True

    # ============ Message 操作 ============

    async def add_message(self, message: Message) -> bool:
        """添加消息"""
        try:
            await self.db.execute(
                """INSERT INTO messages
                   (id, type, from_agent, to_agent, payload, metadata, created_at, delivered_at, read_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (message.id, message.type.value, message.from_agent, message.to_agent,
                 json.dumps(message.payload), json.dumps(message.metadata),
                 message.created_at.isoformat(),
                 message.delivered_at.isoformat() if message.delivered_at else None,
                 message.read_at.isoformat() if message.read_at else None)
            )
            await self.db.commit()
            return True
        except Exception as e:
            print(f"Error adding message: {e}")
            return False

    async def get_messages(self, agent_id: str, limit: int = 100) -> List[Message]:
        """获取Agent的消息历史"""
        messages = []
        async with self.db.execute(
            """SELECT * FROM messages
               WHERE from_agent = ? OR to_agent = ?
               ORDER BY created_at DESC LIMIT ?""",
            (agent_id, agent_id, limit)
        ) as cursor:
            async for row in cursor:
                messages.append(Message(
                    id=row["id"],
                    type=MessageType(row["type"]),
                    from_agent=row["from_agent"],
                    to_agent=row["to_agent"],
                    payload=json.loads(row["payload"]) if row["payload"] else {},
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
                    delivered_at=datetime.fromisoformat(row["delivered_at"]) if row["delivered_at"] else None,
                    read_at=datetime.fromisoformat(row["read_at"]) if row["read_at"] else None
                ))
        return messages

    async def get_conversation(self, agent1: str, agent2: str, limit: int = 50) -> List[Message]:
        """获取两个Agent之间的对话"""
        messages = []
        async with self.db.execute(
            """SELECT * FROM messages
               WHERE (from_agent = ? AND to_agent = ?) OR (from_agent = ? AND to_agent = ?)
               ORDER BY created_at DESC LIMIT ?""",
            (agent1, agent2, agent2, agent1, limit)
        ) as cursor:
            async for row in cursor:
                messages.append(Message(
                    id=row["id"],
                    type=MessageType(row["type"]),
                    from_agent=row["from_agent"],
                    to_agent=row["to_agent"],
                    payload=json.loads(row["payload"]) if row["payload"] else {},
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
                    delivered_at=datetime.fromisoformat(row["delivered_at"]) if row["delivered_at"] else None,
                    read_at=datetime.fromisoformat(row["read_at"]) if row["read_at"] else None
                ))
        return messages

    async def mark_delivered(self, message_id: str) -> bool:
        """标记消息已送达"""
        await self.db.execute(
            "UPDATE messages SET delivered_at = ? WHERE id = ?",
            (datetime.now().isoformat(), message_id)
        )
        await self.db.commit()
        return True

    async def mark_read(self, message_id: str) -> bool:
        """标记消息已读"""
        await self.db.execute(
            "UPDATE messages SET read_at = ? WHERE id = ?",
            (datetime.now().isoformat(), message_id)
        )
        await self.db.commit()
        return True

    # ============ Task 操作 ============

    async def add_task(self, task: Task) -> bool:
        """添加任务"""
        try:
            await self.db.execute(
                """INSERT INTO tasks
                   (id, title, description, from_agent, to_agent, status, priority, result, deadline, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (task.id, task.title, task.description, task.from_agent, task.to_agent,
                 task.status.value, task.priority.value,
                 json.dumps(task.result) if task.result else None,
                 task.deadline.isoformat() if task.deadline else None,
                 task.created_at.isoformat(),
                 task.updated_at.isoformat() if task.updated_at else None)
            )
            await self.db.commit()
            return True
        except Exception as e:
            print(f"Error adding task: {e}")
            return False

    async def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        async with self.db.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return Task(
                    id=row["id"],
                    title=row["title"],
                    description=row["description"],
                    from_agent=row["from_agent"],
                    to_agent=row["to_agent"],
                    status=TaskStatus(row["status"]),
                    priority=Priority(row["priority"]),
                    result=json.loads(row["result"]) if row["result"] else None,
                    deadline=datetime.fromisoformat(row["deadline"]) if row["deadline"] else None,
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
                    updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
                )
        return None

    async def get_tasks(self, agent_id: str, status: Optional[TaskStatus] = None) -> List[Task]:
        """获取Agent的任务"""
        tasks = []
        if status:
            query = "SELECT * FROM tasks WHERE to_agent = ? AND status = ? ORDER BY created_at DESC"
            params = (agent_id, status.value)
        else:
            query = "SELECT * FROM tasks WHERE to_agent = ? ORDER BY created_at DESC"
            params = (agent_id,)

        async with self.db.execute(query, params) as cursor:
            async for row in cursor:
                tasks.append(Task(
                    id=row["id"],
                    title=row["title"],
                    description=row["description"],
                    from_agent=row["from_agent"],
                    to_agent=row["to_agent"],
                    status=TaskStatus(row["status"]),
                    priority=Priority(row["priority"]),
                    result=json.loads(row["result"]) if row["result"] else None,
                    deadline=datetime.fromisoformat(row["deadline"]) if row["deadline"] else None,
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
                    updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
                ))
        return tasks

    async def get_all_tasks(self, limit: int = 100) -> List[Task]:
        """获取所有任务"""
        tasks = []
        query = "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?"
        async with self.db.execute(query, (limit,)) as cursor:
            async for row in cursor:
                tasks.append(Task(
                    id=row["id"],
                    title=row["title"],
                    description=row["description"],
                    from_agent=row["from_agent"],
                    to_agent=row["to_agent"],
                    status=TaskStatus(row["status"]),
                    priority=Priority(row["priority"]),
                    result=json.loads(row["result"]) if row["result"] else None,
                    deadline=datetime.fromisoformat(row["deadline"]) if row["deadline"] else None,
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
                    updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
                ))
        return tasks

    async def update_task_status(self, task_id: str, status: TaskStatus, result: Optional[Dict] = None) -> bool:
        """更新任务状态"""
        if result:
            await self.db.execute(
                "UPDATE tasks SET status = ?, result = ?, updated_at = ? WHERE id = ?",
                (status.value, json.dumps(result), datetime.now().isoformat(), task_id)
            )
        else:
            await self.db.execute(
                "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
                (status.value, datetime.now().isoformat(), task_id)
            )
        await self.db.commit()
        return True

    # ============ Group 操作 ============

    async def add_group(self, group: Group) -> bool:
        """添加群组"""
        try:
            await self.db.execute(
                "INSERT OR REPLACE INTO groups (id, name, description, created_at) VALUES (?, ?, ?, ?)",
                (group.id, group.name, group.description, group.created_at.isoformat())
            )
            # 添加成员
            for member_id in group.members:
                await self.db.execute(
                    "INSERT OR IGNORE INTO group_members (group_id, agent_id) VALUES (?, ?)",
                    (group.id, member_id)
                )
            await self.db.commit()
            return True
        except Exception as e:
            print(f"Error adding group: {e}")
            return False

    async def get_group(self, group_id: str) -> Optional[Group]:
        """获取群组"""
        async with self.db.execute(
            "SELECT * FROM groups WHERE id = ?", (group_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                # 获取成员
                members = []
                async with self.db.execute(
                    "SELECT agent_id FROM group_members WHERE group_id = ?", (group_id,)
                ) as member_cursor:
                    async for member_row in member_cursor:
                        members.append(member_row["agent_id"])

                return Group(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    members=members,
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now()
                )
        return None

    async def get_all_groups(self) -> List[Group]:
        """获取所有群组"""
        groups = []
        async with self.db.execute("SELECT * FROM groups ORDER BY name") as cursor:
            async for row in cursor:
                # 获取成员
                members = []
                async with self.db.execute(
                    "SELECT agent_id FROM group_members WHERE group_id = ?", (row["id"],)
                ) as member_cursor:
                    async for member_row in member_cursor:
                        members.append(member_row["agent_id"])

                groups.append(Group(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    members=members,
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now()
                ))
        return groups

    async def add_group_member(self, group_id: str, agent_id: str) -> bool:
        """添加群组成员"""
        await self.db.execute(
            "INSERT OR IGNORE INTO group_members (group_id, agent_id) VALUES (?, ?)",
            (group_id, agent_id)
        )
        await self.db.commit()
        return True

    async def remove_group_member(self, group_id: str, agent_id: str) -> bool:
        """移除群组成员"""
        await self.db.execute(
            "DELETE FROM group_members WHERE group_id = ? AND agent_id = ?",
            (group_id, agent_id)
        )
        await self.db.commit()
        return True
