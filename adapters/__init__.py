"""Agent适配器模块"""
from .base import BaseAdapter
from .generic import GenericAdapter
from .openclaw import OpenClawAdapter
from .hermes import HermesAdapter

__all__ = [
    'BaseAdapter',
    'GenericAdapter',
    'OpenClawAdapter',
    'HermesAdapter'
]
