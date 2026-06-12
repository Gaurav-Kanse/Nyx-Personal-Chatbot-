"""
automation/tools/file_ops.py
Open, list, move, copy, and (guarded) delete files and folders on Windows.
"""

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List

from automation.base import AutomationTool, ToolMeta, ToolResult
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Paths that can never be deleted via Nyx (safety rail)
_PROTECTED_ROOTS = {
    Path(os.environ.get("SystemRoot", r"C:\Windows")),
    Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
    Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
}


def _is_protected(path: Path) -> bool:
    for root in _PROTECTED_ROOTS:
        try:
            path.resolve().relative_to(root)
            return True
        except ValueError:
            pass
    return False


class FileOpsTool(AutomationTool):
    meta = ToolMeta(
        name="file_ops",
        description="Open files/folders in Explorer, list directory contents, move/copy/delete files.",
        aliases=["file", "folder", "explorer", "ls"],
        examples=["open file C:/notes.txt", "list files C:/Users/User/Desktop", "open folder F:/Prog"],
        dangerous=True,
    )

    def execute(self, args: Dict[str, Any]) -> ToolResult:
        action = args.get("action", "open").lower()

        if action == "open":
            return self._open(args.get("path", ""))
        elif action == "list":
            return self._list(args.get("path", "."))
        elif action == "move":
            return self._move(args.get("src", ""), args.get("dst", ""))
        elif action == "copy":
            return self._copy(args.get("src", ""), args.get("dst", ""))
        elif action == "delete":
            return self._delete(args.get("path", ""), args.get("confirmed", False))
        else:
            return ToolResult(False, f"Unknown file action: {action!r}.")

    # ------------------------------------------------------------------ #

    def _open(self, raw_path: str) -> ToolResult:
        if not raw_path:
            # Open home folder by default
            raw_path = str(Path.home())
        path = Path(raw_path).expanduser()
        if not path.exists():
            return ToolResult(False, f"Path not found: {path}")
        try:
            os.startfile(str(path))
            return ToolResult(True, f"Opened: {path}")
        except Exception as exc:
            return ToolResult(False, f"Could not open {path}: {exc}")

    def _list(self, raw_path: str) -> ToolResult:
        path = Path(raw_path).expanduser()
        if not path.exists():
            return ToolResult(False, f"Directory not found: {path}")
        if not path.is_dir():
            return ToolResult(False, f"Not a directory: {path}")
        try:
            entries: List[str] = []
            for item in sorted(path.iterdir()):
                tag = "[DIR]  " if item.is_dir() else "[FILE] "
                size = ""
                if item.is_file():
                    try:
                        size = f" ({item.stat().st_size:,} bytes)"
                    except OSError:
                        pass
                entries.append(f"  {tag}{item.name}{size}")

            if not entries:
                return ToolResult(True, f"{path} is empty.", speak=True)

            preview = entries[:25]
            suffix = f"\n  … and {len(entries)-25} more" if len(entries) > 25 else ""
            listing = "\n".join(preview) + suffix
            return ToolResult(
                True,
                f"Contents of {path} ({len(entries)} items):\n{listing}",
                data=entries,
                speak=False,
            )
        except PermissionError:
            return ToolResult(False, f"Permission denied: {path}")

    def _move(self, src: str, dst: str) -> ToolResult:
        if not src or not dst:
            return ToolResult(False, "Provide both source and destination paths.")
        s, d = Path(src).expanduser(), Path(dst).expanduser()
        if not s.exists():
            return ToolResult(False, f"Source not found: {s}")
        try:
            shutil.move(str(s), str(d))
            return ToolResult(True, f"Moved {s.name} → {d}")
        except Exception as exc:
            return ToolResult(False, f"Move failed: {exc}")

    def _copy(self, src: str, dst: str) -> ToolResult:
        if not src or not dst:
            return ToolResult(False, "Provide both source and destination paths.")
        s, d = Path(src).expanduser(), Path(dst).expanduser()
        if not s.exists():
            return ToolResult(False, f"Source not found: {s}")
        try:
            if s.is_dir():
                shutil.copytree(str(s), str(d))
            else:
                shutil.copy2(str(s), str(d))
            return ToolResult(True, f"Copied {s.name} → {d}")
        except Exception as exc:
            return ToolResult(False, f"Copy failed: {exc}")

    def _delete(self, raw_path: str, confirmed: bool) -> ToolResult:
        if not raw_path:
            return ToolResult(False, "No path given for deletion.")
        path = Path(raw_path).expanduser().resolve()
        if _is_protected(path):
            return ToolResult(False, f"Refusing to delete protected path: {path}")
        if not path.exists():
            return ToolResult(False, f"Path not found: {path}")
        if not confirmed:
            return ToolResult(
                False,
                f"Delete '{path}'? Type '/delete {path} --confirm' to proceed.",
                speak=True,
            )
        try:
            if path.is_dir():
                shutil.rmtree(str(path))
            else:
                path.unlink()
            return ToolResult(True, f"Deleted: {path}")
        except Exception as exc:
            return ToolResult(False, f"Delete failed: {exc}")
