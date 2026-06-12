"""
automation/registry.py
Central registry that maps tool names (and aliases) to AutomationTool instances.
"""

from typing import Dict, List, Optional
from automation.base import AutomationTool, ToolResult
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ToolRegistry:
    """
    Singleton-style registry for all Nyx automation tools.

    Usage:
        registry = ToolRegistry()
        registry.register(MyTool())
        result = registry.execute("clipboard_read", {})
    """

    def __init__(self):
        self._tools: Dict[str, AutomationTool] = {}   # primary name → tool
        self._aliases: Dict[str, str] = {}             # alias → primary name

    def register(self, tool: AutomationTool) -> None:
        """Register a tool and all its aliases."""
        name = tool.meta.name
        self._tools[name] = tool
        for alias in tool.meta.aliases:
            self._aliases[alias.lower()] = name
        logger.debug(f"Registered automation tool: {name!r} (aliases: {tool.meta.aliases})")

    def get(self, name: str) -> Optional[AutomationTool]:
        """Look up a tool by primary name or alias (case-insensitive)."""
        key = name.lower().strip()
        if key in self._tools:
            return self._tools[key]
        primary = self._aliases.get(key)
        if primary:
            return self._tools.get(primary)
        return None

    def execute(self, name: str, args: dict) -> Optional[ToolResult]:
        """Convenience: look up + execute a tool. Returns None if not found."""
        tool = self.get(name)
        if not tool:
            return None
        try:
            return tool.execute(args)
        except Exception as exc:
            logger.error(f"Tool {name!r} raised: {exc}", exc_info=True)
            return ToolResult(success=False, message=f"Automation error: {exc}", speak=False)

    def list_tools(self) -> List[AutomationTool]:
        return list(self._tools.values())

    def tool_summary(self) -> str:
        """Compact text block injected into the system prompt."""
        lines = ["[AUTOMATION TOOLS AVAILABLE]"]
        for tool in self._tools.values():
            ex = f"  e.g. {tool.meta.examples[0]}" if tool.meta.examples else ""
            lines.append(f"- {tool.meta.name}: {tool.meta.description}{ex}")
        return "\n".join(lines)


def build_registry() -> ToolRegistry:
    """
    Instantiate and register all automation tools.
    Import here (not at module level) to keep startup fast and allow lazy loading.
    """
    from automation.tools.app_launcher   import AppLauncherTool
    from automation.tools.system_control import SystemControlTool
    from automation.tools.clipboard      import ClipboardTool
    from automation.tools.keyboard       import KeyboardTool
    from automation.tools.file_ops       import FileOpsTool
    # pyrefly: ignore [missing-import]
    from automation.tools.web_search     import WebSearchTool

    registry = ToolRegistry()
    for tool_cls in [
        AppLauncherTool,
        SystemControlTool,
        ClipboardTool,
        KeyboardTool,
        FileOpsTool,
        WebSearchTool,
    ]:
        registry.register(tool_cls())
    logger.info(f"ToolRegistry ready — {len(registry.list_tools())} tools loaded.")
    return registry
