"""
core/brain.py
NyxBrain — persistent + transient memory layer.
Delegates all SQL-backed storage to MemoryManager while keeping a
lightweight in-process dict for hot session data (task list, counters).
"""

from typing import Any, Dict, List, Optional
from memory.memory_manager import MemoryManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class NyxBrain:
    """
    Central memory hub for Nyx.

    - Transient data  → Python dict (lost on exit, fast)
    - Persistent data → SQLite via MemoryManager
    """

    def __init__(self):
        # Persistent layer
        self.memory = MemoryManager()

        # Transient session data (reset each run)
        self._session: Dict[str, Any] = {
            "active_tasks": [],
            "session_conversations_count": 0,
            "system_active": True,
        }

        # Load user name from persistent store into session cache
        self._session["user_name"] = self.memory.get_profile("user_name", "User")
        logger.info("NyxBrain online — persistent memory active.")

    # ------------------------------------------------------------------ #
    # TRANSIENT SESSION MEMORY                                             #
    # ------------------------------------------------------------------ #

    def get_memory(self, key: str, default: Any = None) -> Any:
        return self._session.get(key, default)

    def set_memory(self, key: str, value: Any) -> None:
        self._session[key] = value
        logger.debug(f"Session memory: {key} = {value!r}")

    def add_active_task(self, task_name: str) -> None:
        if task_name not in self._session["active_tasks"]:
            self._session["active_tasks"].append(task_name)

    def remove_active_task(self, task_name: str) -> None:
        if task_name in self._session["active_tasks"]:
            self._session["active_tasks"].remove(task_name)

    # ------------------------------------------------------------------ #
    # PERSISTENT PROFILE                                                   #
    # ------------------------------------------------------------------ #

    def get_user_name(self) -> str:
        return self._session["user_name"]

    def set_user_name(self, name: str) -> None:
        self._session["user_name"] = name
        self.memory.set_profile("user_name", name)
        logger.info(f"User name updated to {name!r}")

    def get_profile(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.memory.get_profile(key, default)

    def set_profile(self, key: str, value: str) -> None:
        self.memory.set_profile(key, value)

    # ------------------------------------------------------------------ #
    # CONVERSATION LOGGING                                                 #
    # ------------------------------------------------------------------ #

    def log_user_message(self, content: str) -> None:
        self.memory.log_message("user", content)
        self._session["session_conversations_count"] += 1

    def log_assistant_message(self, content: str) -> None:
        self.memory.log_message("assistant", content)

    # ------------------------------------------------------------------ #
    # NOTES                                                                #
    # ------------------------------------------------------------------ #

    def add_note(self, title: str, content: str, category: str = "general"):
        return self.memory.add_note(title, content, category)

    def get_notes(self, category: Optional[str] = None):
        return self.memory.get_notes(category)

    def delete_note(self, note_id: int) -> bool:
        return self.memory.delete_note(note_id)

    # ------------------------------------------------------------------ #
    # CONTEXT FOR LLM                                                      #
    # ------------------------------------------------------------------ #

    def build_memory_context(self) -> str:
        """Return a compact memory block for system-prompt injection."""
        return self.memory.build_memory_context()

    # ------------------------------------------------------------------ #
    # STATUS                                                               #
    # ------------------------------------------------------------------ #

    def get_status_info(self) -> dict:
        return {
            "user": self.get_user_name(),
            "active_tasks_count": len(self._session["active_tasks"]),
            "session_count": self._session["session_conversations_count"],
        }
