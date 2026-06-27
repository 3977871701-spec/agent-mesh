"""任务引擎模块"""
import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any

from .models import Task, TaskStatus, Priority, MessageType, Message
from .database import Database
from .websocket_server import WebSocketServer

logger = logging.getLogger(__name__)


class TaskEngine:
    def __init__(self, ws_server: WebSocketServer, database: Database):
        self.ws_server = ws_server
        self.db = database
        self.task_handlers: Dict[str, Callable] = {}
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        """启动任务引擎"""
        # 启动定时清理任务
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Task engine started")

    async def stop(self):
        """停止任务引擎"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Task engine stopped")

    async def create_task(
        self,
        title: str,
        from_agent: str,
        to_agent: str,
        description: str = "",
        priority: Priority = Priority.NORMAL,
        deadline: Optional[datetime] = None,
        metadata: Optional[Dict] = None
    ) -> Task:
        """创建新任务"""
        task = Task(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            from_agent=from_agent,
            to_agent=to_agent,
            status=TaskStatus.PENDING,
            priority=priority,
            deadline=deadline,
            created_at=datetime.now()
        )

        # 保存到数据库
        await self.db.add_task(task)

        # 通知目标Agent
        task_notification = Message(
            id=str(uuid.uuid4()),
            type=MessageType.TASK,
            from_agent=from_agent,
            to_agent=to_agent,
            payload={
                "task_id": task.id,
                "title": title,
                "description": description,
                "priority": priority.value,
                "deadline": deadline.isoformat() if deadline else None
            },
            metadata=metadata or {}
        )

        if self.ws_server.is_agent_online(to_agent):
            await self.ws_server.send_to_agent(to_agent, task_notification.to_dict())
            logger.info(f"Task created and notified: {task.id} -> {to_agent}")
        else:
            logger.info(f"Task created (agent offline): {task.id} -> {to_agent}")

        return task

    async def update_task_status(
        self,
        task_id: str,
        agent_id: str,
        status: TaskStatus,
        result: Optional[Dict] = None
    ) -> Optional[Task]:
        """更新任务状态"""
        task = await self.db.get_task(task_id)
        if not task:
            logger.warning(f"Task not found: {task_id}")
            return None

        # 验证权限（只有执行者或创建者可以更新状态）
        if task.to_agent != agent_id and task.from_agent != agent_id:
            logger.warning(f"Agent {agent_id} not authorized to update task {task_id}")
            return None

        # 更新状态
        task.status = status
        task.result = result
        task.updated_at = datetime.now()
        await self.db.update_task_status(task_id, status, result)

        # 通知创建者
        status_update = Message(
            id=str(uuid.uuid4()),
            type=MessageType.TASK_UPDATE,
            from_agent=agent_id,
            to_agent=task.from_agent,
            payload={
                "task_id": task_id,
                "status": status.value,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        )

        if self.ws_server.is_agent_online(task.from_agent):
            await self.ws_server.send_to_agent(task.from_agent, status_update.to_dict())

        logger.info(f"Task {task_id} status updated to {status.value} by {agent_id}")
        return task

    async def start_task(self, task_id: str, agent_id: str) -> Optional[Task]:
        """开始执行任务"""
        return await self.update_task_status(task_id, agent_id, TaskStatus.IN_PROGRESS)

    async def complete_task(self, task_id: str, agent_id: str, result: Dict) -> Optional[Task]:
        """完成任务"""
        return await self.update_task_status(task_id, agent_id, TaskStatus.COMPLETED, result)

    async def fail_task(self, task_id: str, agent_id: str, error: str) -> Optional[Task]:
        """任务失败"""
        return await self.update_task_status(task_id, agent_id, TaskStatus.FAILED, {"error": error})

    async def cancel_task(self, task_id: str, agent_id: str) -> Optional[Task]:
        """取消任务"""
        return await self.update_task_status(task_id, agent_id, TaskStatus.CANCELLED)

    async def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务详情"""
        return await self.db.get_task(task_id)

    async def get_agent_tasks(
        self,
        agent_id: str,
        status: Optional[TaskStatus] = None
    ) -> List[Task]:
        """获取Agent的任务列表"""
        return await self.db.get_tasks(agent_id, status)

    async def get_pending_tasks(self, agent_id: str) -> List[Task]:
        """获取待处理任务"""
        return await self.get_agent_tasks(agent_id, TaskStatus.PENDING)

    async def get_in_progress_tasks(self, agent_id: str) -> List[Task]:
        """获取进行中的任务"""
        return await self.get_agent_tasks(agent_id, TaskStatus.IN_PROGRESS)

    async def get_completed_tasks(self, agent_id: str) -> List[Task]:
        """获取已完成的任务"""
        return await self.get_agent_tasks(agent_id, TaskStatus.COMPLETED)

    async def reassign_task(self, task_id: str, new_agent: str, operator: str) -> Optional[Task]:
        """重新分配任务"""
        task = await self.db.get_task(task_id)
        if not task:
            return None

        old_agent = task.to_agent
        task.to_agent = new_agent
        task.status = TaskStatus.ASSIGNED
        task.updated_at = datetime.now()

        await self.db.update_task_status(task_id, TaskStatus.ASSIGNED)

        # 通知新执行者
        notification = Message(
            id=str(uuid.uuid4()),
            type=MessageType.TASK,
            from_agent=operator,
            to_agent=new_agent,
            payload={
                "task_id": task_id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority.value,
                "reassigned_from": old_agent
            }
        )

        if self.ws_server.is_agent_online(new_agent):
            await self.ws_server.send_to_agent(new_agent, notification.to_dict())

        logger.info(f"Task {task_id} reassigned from {old_agent} to {new_agent} by {operator}")
        return task

    async def _cleanup_loop(self):
        """定时清理过期任务"""
        while True:
            try:
                await asyncio.sleep(3600)  # 每小时检查一次
                # 这里可以添加清理逻辑，比如标记超时任务
                logger.debug("Task cleanup completed")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Task cleanup error: {e}")

    def register_task_handler(self, task_type: str, handler: Callable):
        """注册任务处理器"""
        self.task_handlers[task_type] = handler

    async def get_task_statistics(self, agent_id: Optional[str] = None) -> Dict[str, int]:
        """获取任务统计"""
        # 这里简化实现，实际应该从数据库统计
        stats = {
            "pending": 0,
            "assigned": 0,
            "in_progress": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0
        }

        if agent_id:
            for status in TaskStatus:
                tasks = await self.db.get_tasks(agent_id, status)
                stats[status.value] = len(tasks)
        else:
            # 统计所有任务
            all_agents = await self.db.get_all_agents()
            for agent in all_agents:
                for status in TaskStatus:
                    tasks = await self.db.get_tasks(agent.id, status)
                    stats[status.value] += len(tasks)

        return stats
