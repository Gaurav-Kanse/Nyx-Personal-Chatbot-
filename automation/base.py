"""
automation/base.py
Base types shared across all automation tools.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ToolResult:
    """Returned by every AutomationTool.execute() call."""
    success: bool
    message: str                       # Human-readable reply shown to user
    data: Optional[Any] = None         # Optional structured payload (lists, dicts…)
    speak: bool = True                 # Whether TTS should read this aloud


@dataclass
class ToolMeta:
    name: str
    description: str
    aliases: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    dangerous: bool = False            # Requires confirmation if True


class AutomationTool(ABC):
    """
    Abstract base for every Nyx automation tool.

    Subclasses must:
      - Set  meta: ToolMeta
      - Implement execute(args: dict) -> ToolResult
    """
    meta: ToolMeta

    @abstractmethod
    def execute(self, args: Dict[str, Any]) -> ToolResult:
        ...

    def __repr__(self) -> str:
        return f"<AutomationTool: {self.meta.name}>"
