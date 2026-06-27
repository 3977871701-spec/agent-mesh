"""配置管理模块"""
import os
import yaml
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 18800
    max_connections: int = 100
    heartbeat_interval: int = 30  # seconds
    heartbeat_timeout: int = 90  # seconds


@dataclass
class DatabaseConfig:
    path: str = "./data/agent_mesh.db"


@dataclass
class DiscoveryConfig:
    auto_discover: bool = True
    scan_paths: List[str] = field(default_factory=lambda: [
        "~/.openclaw/agents/",
        "~/.hermes/",
        "~/.codex/"
    ])
    confirm_required: bool = True


@dataclass
class AdapterConfig:
    enabled: bool = True
    cli_path: Optional[str] = None
    gateway: Optional[str] = None
    token: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: str = "./logs/agent_mesh.log"
    max_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


@dataclass
class WebConfig:
    enabled: bool = True
    host: str = "127.0.0.1"
    port: int = 18801


@dataclass
class Config:
    server: ServerConfig = field(default_factory=ServerConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    discovery: DiscoveryConfig = field(default_factory=DiscoveryConfig)
    adapters: Dict[str, AdapterConfig] = field(default_factory=dict)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    web: WebConfig = field(default_factory=WebConfig)

    @classmethod
    def load(cls, config_path: str) -> 'Config':
        """从YAML文件加载配置"""
        if not os.path.exists(config_path):
            return cls()

        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}

        config = cls()

        # 服务器配置
        if 'server' in data:
            server = data['server']
            config.server = ServerConfig(
                host=server.get('host', config.server.host),
                port=server.get('port', config.server.port),
                max_connections=server.get('max_connections', config.server.max_connections),
                heartbeat_interval=server.get('heartbeat_interval', config.server.heartbeat_interval),
                heartbeat_timeout=server.get('heartbeat_timeout', config.server.heartbeat_timeout)
            )

        # 数据库配置
        if 'database' in data:
            db = data['database']
            config.database = DatabaseConfig(
                path=db.get('path', config.database.path)
            )

        # 发现配置
        if 'discovery' in data:
            disc = data['discovery']
            config.discovery = DiscoveryConfig(
                auto_discover=disc.get('auto_discover', config.discovery.auto_discover),
                scan_paths=disc.get('scan_paths', config.discovery.scan_paths),
                confirm_required=disc.get('confirm_required', config.discovery.confirm_required)
            )

        # 适配器配置
        if 'adapters' in data:
            for name, adapter_data in data['adapters'].items():
                config.adapters[name] = AdapterConfig(
                    enabled=adapter_data.get('enabled', True),
                    cli_path=adapter_data.get('cli_path'),
                    gateway=adapter_data.get('gateway'),
                    token=adapter_data.get('token'),
                    extra=adapter_data.get('extra', {})
                )

        # 日志配置
        if 'logging' in data:
            log = data['logging']
            config.logging = LoggingConfig(
                level=log.get('level', config.logging.level),
                file=log.get('file', config.logging.file),
                max_size=log.get('max_size', config.logging.max_size),
                backup_count=log.get('backup_count', config.logging.backup_count)
            )

        # Web配置
        if 'web' in data:
            web = data['web']
            config.web = WebConfig(
                enabled=web.get('enabled', config.web.enabled),
                host=web.get('host', config.web.host),
                port=web.get('port', config.web.port)
            )

        return config

    def save(self, config_path: str):
        """保存配置到YAML文件"""
        data = {
            'server': {
                'host': self.server.host,
                'port': self.server.port,
                'max_connections': self.server.max_connections,
                'heartbeat_interval': self.server.heartbeat_interval,
                'heartbeat_timeout': self.server.heartbeat_timeout
            },
            'database': {
                'path': self.database.path
            },
            'discovery': {
                'auto_discover': self.discovery.auto_discover,
                'scan_paths': self.discovery.scan_paths,
                'confirm_required': self.discovery.confirm_required
            },
            'adapters': {},
            'logging': {
                'level': self.logging.level,
                'file': self.logging.file,
                'max_size': self.logging.max_size,
                'backup_count': self.logging.backup_count
            },
            'web': {
                'enabled': self.web.enabled,
                'host': self.web.host,
                'port': self.web.port
            }
        }

        # 适配器配置
        for name, adapter in self.adapters.items():
            data['adapters'][name] = {
                'enabled': adapter.enabled,
                'cli_path': adapter.cli_path,
                'gateway': adapter.gateway,
                'token': adapter.token,
                'extra': adapter.extra
            }

        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
