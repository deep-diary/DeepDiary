"""
DeepWin 记忆管理模块

基于 mem0 库实现的长期记忆存储和检索系统。
支持多种记忆类型，包括语义记忆、情景记忆和程序性记忆。
"""

from .memory_client_wrapper import MemoryManager
from .config import (
    create_memory_manager,
    create_sample_messages,
    add_memory_to_system,
    search_memories,
    get_all_memories,
    main
)

__all__ = [
    'MemoryManager',
    'create_memory_manager',
    'create_sample_messages', 
    'add_memory_to_system',
    'search_memories',
    'get_all_memories',
    'main'
]

__version__ = "1.2.0"
__author__ = "DeepWin Team"
__description__ = "DeepWin 记忆管理模块 - 基于 mem0 的长期记忆系统"
