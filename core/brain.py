from typing import Dict, Any
from utils.logger import setup_logger

logger = setup_logger(__name__)

class NyxBrain:
    def __init__(self):
        # Transient in-memory storage for Phase 1
        self.transient_memory: Dict[str, Any] = {
            "user_name": "User",
            "active_tasks": [],
            "session_conversations_count": 0,
            "system_active": True
        }
        logger.info("NyxBrain initialized in transient session mode.")

    def get_memory(self, key: str, default: Any = None) -> Any:
        return self.transient_memory.get(key, default)

    def set_memory(self, key: str, value: Any):
        self.transient_memory[key] = value
        logger.debug(f"Brain memory update: {key} = {value}")

    def add_active_task(self, task_name: str):
        if task_name not in self.transient_memory["active_tasks"]:
            self.transient_memory["active_tasks"].append(task_name)

    def remove_active_task(self, task_name: str):
        if task_name in self.transient_memory["active_tasks"]:
            self.transient_memory["active_tasks"].remove(task_name)

    def get_status_info(self) -> dict:
        return {
            "user": self.get_memory("user_name"),
            "active_tasks_count": len(self.get_memory("active_tasks")),
            "session_count": self.get_memory("session_conversations_count")
        }
