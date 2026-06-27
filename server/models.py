"""数据模型定义"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import uuid


class AgentStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"


class MessageType(str, Enum):
    REGISTER = "register"
    MESSAGE = "message"
    BROADCAST = "broadcast"
    TASK = "task"
    TASK_UPDATE = "task_update"
    ACK = "ack"
    HEARTBEAT = "heartbeat"
    DISCOVER = "discover"
    DISCOVER_RESPONSE = "discover_response"


class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class Agent:
    id: str
    name: str
    type: str  # hermes|openclaw|codex|custom
    status: AgentStatus = AgentStatus.OFFLINE
    capabilities: List[str] = field(default_factory=list)
    endpoint: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_seen: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "status": self.status.value,
            "capabilities": self.capabilities,
            "endpoint": self.endpoint,
            "metadata": self.metadata,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Agent':
        return cls(
            id=data["id"],
            name=data["name"],
            type=data["type"],
            status=AgentStatus(data.get("status", "offline")),
            capabilities=data.get("capabilities", []),
            endpoint=data.get("endpoint"),
            metadata=data.get("metadata", {}),
            last_seen=datetime.fromisoformat(data["last_seen"]) if data.get("last_seen") else None,
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now()
        )


@dataclass
class Message:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.MESSAGE
    from_agent: str = ""
    to_agent: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "from": self.from_agent,
            "to": self.to_agent,
            "payload": self.payload,
            "metadata": self.metadata,
            "timestamp": self.created_at.isoformat(),
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        # Handle ISO timestamp with Z suffix
        timestamp = data.get("timestamp")
        if timestamp:
            timestamp = timestamp.replace('Z', '+00:00')

        delivered_at = data.get("delivered_at")
        if delivered_at:
            delivered_at = delivered_at.replace('Z', '+00:00')

        read_at = data.get("read_at")
        if read_at:
            read_at = read_at.replace('Z', '+00:00')

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            type=MessageType(data.get("type", "message")),
            from_agent=data.get("from", ""),
            to_agent=data.get("to", ""),
            payload=data.get("payload", {}),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(timestamp) if timestamp else datetime.now(),
            delivered_at=datetime.fromisoformat(delivered_at) if delivered_at else None,
            read_at=datetime.fromisoformat(read_at) if read_at else None
        )


@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    from_agent: str = ""
    to_agent: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.NORMAL
    result: Optional[Dict[str, Any]] = None
    deadline: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "status": self.status.value,
            "priority": self.priority.value,
            "result": self.result,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data.get("title", ""),
            description=data.get("description", ""),
            from_agent=data.get("from_agent", ""),
            to_agent=data.get("to_agent", ""),
            status=TaskStatus(data.get("status", "pending")),
            priority=Priority(data.get("priority", "normal")),
            result=data.get("result"),
            deadline=datetime.fromisoformat(data["deadline"]) if data.get("deadline") else None,
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )


@dataclass
class Group:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    members: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "members": self.members,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Group':
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            members=data.get("members", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now()
        )
