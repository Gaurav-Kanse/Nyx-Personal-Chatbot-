"""
automation/tools/system_control.py
System-level controls: volume, screen lock, shutdown/restart/sleep.
Uses Windows built-in mechanisms (nircmdc for volume, subprocess for power).
"""

import os
import subprocess
import shutil
import urllib.request
from pathlib import Path
from typing import Any, Dict

from automation.base import AutomationTool, ToolMeta, ToolResult
from core.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

# nircmdc is a tiny free CLI tool for volume/brightness control on Windows
_NIRCMD_URL  = "https://www.nirsoft.net/utils/nircmdc.exe"
_NIRCMD_PATH = Path(Config.BASE_DIR) / "temp" / "nircmdc.exe"


def _ensure_nircmd() -> bool:
    """Download nircmdc.exe to temp/ if not already present."""
    if _NIRCMD_PATH.exists():
        return True
    try:
        _NIRCMD_PATH.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Downloading nircmdc.exe for volume control…")
        urllib.request.urlretrieve(_NIRCMD_URL, str(_NIRCMD_PATH))
        logger.info("nircmdc.exe downloaded successfully.")
        return True
    except Exception as exc:
        logger.warning(f"Could not download nircmdc.exe: {exc}. Volume control unavailable.")
        return False


def _nircmd(*args) -> bool:
    """Run a nircmdc command. Returns True on success."""
    if not _ensure_nircmd():
        return False
    try:
        subprocess.run(
            [str(_NIRCMD_PATH), *args],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception as exc:
        logger.error(f"nircmdc error: {exc}")
        return False


def _powershell(cmd: str) -> bool:
    """Run a PowerShell one-liner silently."""
    try:
        subprocess.run(
            ["powershell", "-NonInteractive", "-Command", cmd],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception as exc:
        logger.error(f"PowerShell error: {exc}")
        return False


class SystemControlTool(AutomationTool):
    meta = ToolMeta(
        name="system_control",
        description="Control system volume, lock screen, shutdown, restart, or sleep the PC.",
        aliases=["volume", "power", "lock", "sleep"],
        examples=["volume 50", "lock screen", "shutdown"],
        dangerous=True,
    )

    def execute(self, args: Dict[str, Any]) -> ToolResult:
        action = args.get("action", "").lower()

        # ── Volume ──────────────────────────────────────────────────────
        if action == "set":
            level = max(0, min(100, int(args.get("level", 50))))
            # nircmdc uses 0–65535 scale
            nircmd_vol = int(level / 100 * 65535)
            ok = _nircmd("setsysvolume", str(nircmd_vol))
            if not ok:
                # Fallback: PowerShell via COM
                ok = _powershell(
                    f"(New-Object -ComObject WScript.Shell).SendKeys([char]173);"  # noop
                    f"$vol=[Math]::Round({level}/100*65535);"
                    f"(New-Object -com 'WScript.Shell');"
                )
            return ToolResult(ok, f"Volume set to {level}%." if ok else "Could not set volume.")

        elif action in ("up", "volumeup"):
            ok = _nircmd("changesysvolume", "4000")
            return ToolResult(ok, "Volume increased." if ok else "Volume control unavailable.")

        elif action in ("down", "volumedown"):
            ok = _nircmd("changesysvolume", "-4000")
            return ToolResult(ok, "Volume decreased." if ok else "Volume control unavailable.")

        elif action in ("mute", "unmute"):
            ok = _nircmd("mutesysvolume", "2")  # 2 = toggle
            return ToolResult(ok, "Volume toggled mute." if ok else "Mute toggle failed.")

        elif action == "get":
            return ToolResult(True, "I can set the volume — try '/volume 50' or 'volume up'.", speak=True)

        # ── Screen lock ─────────────────────────────────────────────────
        elif action in ("lock", "lock screen"):
            ok = _powershell("Invoke-Expression 'rundll32 user32.dll,LockWorkStation'")
            if not ok:
                try:
                    import ctypes
                    ctypes.windll.user32.LockWorkStation()
                    ok = True
                except Exception:
                    ok = False
            return ToolResult(ok, "Screen locked." if ok else "Could not lock screen.")

        # ── Sleep ────────────────────────────────────────────────────────
        elif action == "sleep":
            ok = _nircmd("standby") or _powershell(
                "Add-Type -Assembly System.Windows.Forms;"
                "[System.Windows.Forms.Application]::SetSuspendState('Suspend',$false,$false)"
            )
            return ToolResult(ok, "Going to sleep." if ok else "Sleep command failed.")

        # ── Shutdown (guarded) ───────────────────────────────────────────
        elif action == "shutdown":
            if not args.get("confirmed"):
                return ToolResult(
                    False,
                    "Shutdown requested. Type '/shutdown --confirm' to proceed.",
                    speak=True,
                )
            ok = _powershell("Stop-Computer -Force")
            return ToolResult(ok, "Shutting down…" if ok else "Shutdown failed.")

        elif action == "shutdown_confirmed":
            ok = _powershell("Stop-Computer -Force")
            return ToolResult(ok, "Shutting down…")

        # ── Restart (guarded) ────────────────────────────────────────────
        elif action in ("restart", "reboot"):
            if not args.get("confirmed"):
                return ToolResult(
                    False,
                    "Restart requested. Type '/restart --confirm' to proceed.",
                    speak=True,
                )
            ok = _powershell("Restart-Computer -Force")
            return ToolResult(ok, "Restarting…" if ok else "Restart failed.")

        else:
            return ToolResult(False, f"Unknown system action: {action!r}.")
