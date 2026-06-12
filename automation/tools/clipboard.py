"""
automation/tools/clipboard.py
Read, write, and clear the Windows clipboard via pyperclip.
"""

from typing import Any, Dict
from automation.base import AutomationTool, ToolMeta, ToolResult
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ClipboardTool(AutomationTool):
    meta = ToolMeta(
        name="clipboard",
        description="Read text from the clipboard, copy text to it, or clear it.",
        aliases=["clip", "paste"],
        examples=["read clipboard", "copy Hello World", "clear clipboard"],
    )

    def execute(self, args: Dict[str, Any]) -> ToolResult:
        try:
            import pyperclip
        except ImportError:
            return ToolResult(False, "pyperclip is not installed. Run: pip install pyperclip")

        action = args.get("action", "read").lower()

        if action == "read":
            text = pyperclip.paste()
            if not text:
                return ToolResult(True, "The clipboard is currently empty.", speak=True)
            preview = text[:200]
            suffix = "…" if len(text) > 200 else ""
            return ToolResult(True, f"Clipboard contains: {preview}{suffix}", data=text, speak=True)

        elif action == "write":
            text = args.get("text", "")
            if not text:
                return ToolResult(False, "Nothing to copy — provide some text.")
            pyperclip.copy(text)
            return ToolResult(True, f"Copied to clipboard: {text[:60]}{'…' if len(text)>60 else ''}")

        elif action == "clear":
            pyperclip.copy("")
            return ToolResult(True, "Clipboard cleared.")

        else:
            return ToolResult(False, f"Unknown clipboard action: {action!r}.")
