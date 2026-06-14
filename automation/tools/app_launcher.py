"""
automation/tools/app_launcher.py
Open / close / list applications on Windows.
Resolves app names via a curated alias map, PATH lookup, and the nyx.db app_usage table.
"""

import os
import subprocess
import shutil
from typing import Any, Dict, Optional

import psutil

from automation.base import AutomationTool, ToolMeta, ToolResult
from utils.logger import setup_logger

logger = setup_logger(__name__)

# ---------------------------------------------------------------------------
# Curated alias map  (lowercase key → executable name or full path)
# ---------------------------------------------------------------------------
APP_ALIASES: Dict[str, str] = {
    # Browsers
    "chrome":          "chrome.exe",
    "google chrome":   "chrome.exe",
    "firefox":         "firefox.exe",
    "edge":            "msedge.exe",
    "microsoft edge":  "msedge.exe",
    "brave":           "brave.exe",

    # Editors / IDEs
    "vscode":          "code.exe",
    "vs code":         "code.exe",
    "visual studio code": "code.exe",
    "notepad":         "notepad.exe",
    "notepad++":       "notepad++.exe",
    "sublime":         "sublime_text.exe",
    "pycharm":         "pycharm64.exe",

    # Windows built-ins
    "explorer":        "explorer.exe",
    "file explorer":   "explorer.exe",
    "calculator":      "calc.exe",
    "calc":            "calc.exe",
    "paint":           "mspaint.exe",
    "task manager":    "taskmgr.exe",
    "taskmgr":         "taskmgr.exe",
    "cmd":             "cmd.exe",
    "command prompt":  "cmd.exe",
    "powershell":      "powershell.exe",
    "terminal":        "wt.exe",
    "windows terminal":"wt.exe",
    "wordpad":         "wordpad.exe",
    "snipping tool":   "snippingtool.exe",
    "snip":            "snippingtool.exe",
    "clock":           "ms-clock:",       # UWP protocol
    "settings":        "ms-settings:",
    "store":           "ms-windows-store:",

    # Media
    "vlc":             "vlc.exe",
    "spotify":         "spotify.exe",
    "media player":    "wmplayer.exe",

    # Communication
    "discord":         "discord.exe",
    "slack":           "slack.exe",
    "teams":           "teams.exe",
    "zoom":            "zoom.exe",
    "telegram":        "telegram.exe",
    "whatsapp":        "whatsapp.exe",

    # Dev tools
    "git bash":        "git-bash.exe",
    "docker":          "docker desktop.exe",
    "postman":         "postman.exe",
    "obsidian":        "obsidian.exe",
    "notion":          "notion.exe",
}

# Common installation prefixes to search when shutil.which() misses
_SEARCH_PREFIXES = [
    os.path.expandvars(r"%ProgramFiles%"),
    os.path.expandvars(r"%ProgramFiles(x86)%"),
    os.path.expandvars(r"%LocalAppData%"),
    os.path.expandvars(r"%AppData%"),
]


def _resolve_executable(app_name: str) -> Optional[str]:
    """Try to find an executable path for the given app name."""
    key = app_name.lower().strip()

    # 1. Direct alias
    exe = APP_ALIASES.get(key)
    if not exe:
        # Try partial alias match
        for alias, e in APP_ALIASES.items():
            if key in alias or alias in key:
                exe = e
                break

    if not exe:
        exe = app_name  # Use as-is

    # 2. UWP protocol (ms-settings:, ms-clock:, etc.)
    if exe.endswith(":"):
        return exe

    # 3. shutil.which (checks PATH)
    found = shutil.which(exe)
    if found:
        return found

    # 4. Walk common install dirs for the exe name
    for prefix in _SEARCH_PREFIXES:
        if not os.path.isdir(prefix):
            continue
        for root, _dirs, files in os.walk(prefix):
            if exe.lower() in [f.lower() for f in files]:
                return os.path.join(root, exe)

    return None


class AppLauncherTool(AutomationTool):
    meta = ToolMeta(
        name="app_launcher",
        description="Open or close applications by name, or list running processes.",
        aliases=["open_app", "launch_app", "close_app"],
        examples=["open notepad", "close chrome", "list running apps"],
    )

    def execute(self, args: Dict[str, Any]) -> ToolResult:
        action = args.get("action", "open").lower()

        if action == "list":
            return self._list_running()
        elif action == "open":
            return self._open(args.get("app", ""))
        elif action == "close":
            return self._close(args.get("app", ""))
        else:
            return ToolResult(False, f"Unknown app_launcher action: {action!r}")

    # ------------------------------------------------------------------ #

    def _open(self, app_name: str) -> ToolResult:
        if not app_name:
            return ToolResult(False, "Please specify an app to open.")

        # Check if the input itself is an existing file or directory path
        expanded_name = os.path.expandvars(os.path.expanduser(app_name))
        if os.path.exists(expanded_name):
            try:
                os.startfile(expanded_name)
                # Track in memory DB
                try:
                    from memory.memory_manager import MemoryManager
                    MemoryManager().record_app_launch(app_name, expanded_name)
                except Exception:
                    pass
                return ToolResult(True, f"Opened: {app_name}", speak=True)
            except Exception as exc:
                logger.error(f"AppLauncher open path error: {exc}")
                return ToolResult(False, f"Failed to open path {app_name}: {exc}")

        path = _resolve_executable(app_name)

        if not path:
            return ToolResult(
                False,
                f"I couldn't find '{app_name}' on your system. "
                "Is it installed? Try giving the full path.",
            )

        try:
            # UWP/protocol handlers (e.g. ms-settings:)
            if path.endswith(":") or ":" in path and path.index(":") > 1:
                os.startfile(path)
            else:
                subprocess.Popen(
                    [path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                )

            # Track in memory DB (lazy import to avoid circular at startup)
            try:
                from memory.memory_manager import MemoryManager
                MemoryManager().record_app_launch(app_name, path)
            except Exception:
                pass

            return ToolResult(True, f"Opened {app_name}.", speak=True)
        except Exception as exc:
            logger.error(f"AppLauncher open error: {exc}")
            return ToolResult(False, f"Failed to open {app_name}: {exc}")

    def _close(self, app_name: str) -> ToolResult:
        if not app_name:
            return ToolResult(False, "Please specify an app to close.")

        key = app_name.lower().strip()
        killed = []

        for proc in psutil.process_iter(["pid", "name"]):
            try:
                pname = proc.info["name"].lower()
                if key in pname or pname.startswith(key.replace(" ", "")):
                    proc.terminate()
                    killed.append(proc.info["name"])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        if killed:
            return ToolResult(True, f"Closed: {', '.join(set(killed))}.")
        return ToolResult(False, f"No running process found matching '{app_name}'.")

    def _list_running(self) -> ToolResult:
        seen = set()
        names = []
        for proc in psutil.process_iter(["name"]):
            try:
                n = proc.info["name"]
                if n and n not in seen:
                    seen.add(n)
                    names.append(n)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        names.sort()
        summary = ", ".join(names[:30])
        return ToolResult(
            True,
            f"Running processes ({len(names)} total): {summary}…",
            data=names,
            speak=False,
        )
