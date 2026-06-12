"""
automation/tools/keyboard.py
Type text, press hotkeys, and take screenshots via pyautogui.
"""

import time
from pathlib import Path
from typing import Any, Dict

from automation.base import AutomationTool, ToolMeta, ToolResult
from core.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Screenshot save location
_SCREENSHOT_DIR = Path(Config.BASE_DIR) / "data" / "screenshots"


class KeyboardTool(AutomationTool):
    meta = ToolMeta(
        name="keyboard",
        description="Type text into the focused window, press hotkeys, or take a screenshot.",
        aliases=["type", "press", "hotkey", "screenshot"],
        examples=["type Hello World", "press ctrl+c", "screenshot"],
    )

    def execute(self, args: Dict[str, Any]) -> ToolResult:
        try:
            import pyautogui
            pyautogui.FAILSAFE = True   # Move mouse to top-left corner to abort
            pyautogui.PAUSE = 0.05
        except ImportError:
            return ToolResult(False, "pyautogui is not installed. Run: pip install pyautogui")

        action = args.get("action", "type").lower()

        if action == "type":
            text = args.get("text", "")
            if not text:
                return ToolResult(False, "Nothing to type — provide some text.")
            try:
                time.sleep(0.3)  # Give user time to focus the target window
                pyautogui.typewrite(text, interval=0.03)
                return ToolResult(True, f"Typed: {text[:60]}{'…' if len(text)>60 else ''}")
            except Exception as exc:
                return ToolResult(False, f"Typing failed: {exc}")

        elif action in ("hotkey", "press"):
            keys_raw = args.get("keys", "")
            if not keys_raw:
                return ToolResult(False, "No keys specified.")
            # Support formats: "ctrl+c", "ctrl c", "alt+f4"
            keys = [k.strip() for k in keys_raw.replace("+", " ").split()]
            try:
                pyautogui.hotkey(*keys)
                return ToolResult(True, f"Pressed: {'+'.join(keys)}")
            except Exception as exc:
                return ToolResult(False, f"Hotkey failed: {exc}")

        elif action == "screenshot":
            try:
                _SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
                ts = time.strftime("%Y%m%d_%H%M%S")
                path = _SCREENSHOT_DIR / f"nyx_screenshot_{ts}.png"
                img = pyautogui.screenshot()
                img.save(str(path))
                return ToolResult(
                    True,
                    f"Screenshot saved to: {path}",
                    data=str(path),
                    speak=True,
                )
            except Exception as exc:
                return ToolResult(False, f"Screenshot failed: {exc}")

        else:
            return ToolResult(False, f"Unknown keyboard action: {action!r}.")
