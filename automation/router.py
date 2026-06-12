"""
automation/router.py
Lightweight keyword/regex intent router.
Sits BEFORE the LLM — zero inference overhead for obvious automation commands.
Falls through to LLM if no rule matches.
"""

import re
from typing import Optional, Tuple, Dict, Any
from automation.base import ToolResult
from utils.logger import setup_logger

logger = setup_logger(__name__)

# ---------------------------------------------------------------------------
# Intent rules table
# Each entry: (regex_pattern, tool_name, arg_extractor_fn)
# arg_extractor receives the re.Match object and returns a dict for tool.execute()
# ---------------------------------------------------------------------------

def _text_arg(m: re.Match) -> Dict[str, Any]:
    return {"text": m.group("arg").strip() if m.group("arg") else ""}

def _app_open_arg(m: re.Match) -> Dict[str, Any]:
    return {"action": "open", "app": m.group("arg").strip()}

def _app_close_arg(m: re.Match) -> Dict[str, Any]:
    return {"action": "close", "app": m.group("arg").strip()}

def _volume_arg(m: re.Match) -> Dict[str, Any]:
    raw = (m.group("arg") or "").strip().lower()
    if raw.isdigit():
        return {"action": "set", "level": int(raw)}
    return {"action": raw or "get"}   # up / down / mute / get

def _search_arg(m: re.Match) -> Dict[str, Any]:
    return {"query": m.group("arg").strip(), "engine": "duckduckgo"}

def _url_arg(m: re.Match) -> Dict[str, Any]:
    return {"url": m.group("arg").strip()}

def _youtube_arg(m: re.Match) -> Dict[str, Any]:
    return {"query": m.group("arg").strip(), "engine": "youtube"}

def _file_open_arg(m: re.Match) -> Dict[str, Any]:
    return {"action": "open", "path": m.group("arg").strip()}

def _file_list_arg(m: re.Match) -> Dict[str, Any]:
    return {"action": "list", "path": (m.group("arg") or ".").strip()}

def _clipboard_read(_: re.Match) -> Dict[str, Any]:
    return {"action": "read"}

def _clipboard_copy(m: re.Match) -> Dict[str, Any]:
    return {"action": "write", "text": m.group("arg").strip()}

def _clipboard_clear(_: re.Match) -> Dict[str, Any]:
    return {"action": "clear"}

def _hotkey_arg(m: re.Match) -> Dict[str, Any]:
    return {"action": "hotkey", "keys": m.group("arg").strip()}

def _screenshot_arg(_: re.Match) -> Dict[str, Any]:
    return {"action": "screenshot"}

def _system_arg(m: re.Match) -> Dict[str, Any]:
    return {"action": m.group("action").lower()}

def _apps_running(_: re.Match) -> Dict[str, Any]:
    return {"action": "list"}


# (pattern, tool_name, arg_fn)
_RULES = [
    # App launching
    (r"^(?:open|launch|start|run)\s+(?P<arg>.+)$",              "app_launcher",    _app_open_arg),
    (r"^(?:close|kill|quit|stop)\s+(?P<arg>.+)$",               "app_launcher",    _app_close_arg),
    (r"^(?:list|show)\s+(?:running\s+)?apps?$",                 "app_launcher",    _apps_running),

    # Volume
    (r"^volume\s+(?P<arg>\S+)$",                                "system_control",  _volume_arg),
    (r"^(?:set\s+)?volume\s+(?:to\s+)?(?P<arg>\d+)%?$",        "system_control",  _volume_arg),
    (r"^(?:mute|unmute)$",                                       "system_control",  lambda m: {"action": m.group(0).lower()}),

    # System power
    (r"^(?P<action>shutdown|restart|reboot|sleep|lock(?:\s+screen)?)$",
                                                                 "system_control",  _system_arg),
    (r"^(?:lock|lock\s+(?:the\s+)?(?:screen|pc|computer))$",   "system_control",  lambda _: {"action": "lock"}),

    # Web search
    (r"^(?:search|google|look\s+up|find)\s+(?P<arg>.+)$",       "web_search",      _search_arg),
    (r"^(?:youtube|yt)\s+(?P<arg>.+)$",                         "web_search",      _youtube_arg),
    (r"^(?:open|go\s+to)\s+(?P<arg>https?://\S+)$",             "web_search",      _url_arg),

    # Clipboard
    (r"^(?:what(?:'s|\s+is)\s+(?:in\s+)?(?:my\s+)?clipboard|read\s+clipboard|clipboard\s+read)$",
                                                                 "clipboard",       _clipboard_read),
    (r"^(?:copy|clipboard\s+copy)\s+(?P<arg>.+)$",              "clipboard",       _clipboard_copy),
    (r"^(?:clear\s+clipboard|clipboard\s+clear)$",              "clipboard",       _clipboard_clear),

    # Keyboard / type
    (r"^type\s+(?P<arg>.+)$",                                   "keyboard",        _text_arg),
    (r"^(?:press|hotkey)\s+(?P<arg>.+)$",                       "keyboard",        _hotkey_arg),
    (r"^(?:take\s+a?\s*)?screenshot$",                          "keyboard",        _screenshot_arg),

    # File operations
    (r"^(?:open\s+(?:file|folder|directory)|explorer)\s+(?P<arg>.+)$",
                                                                 "file_ops",        _file_open_arg),
    (r"^(?:list\s+files?(?:\s+in)?|ls)\s*(?P<arg>.*)?$",        "file_ops",        _file_list_arg),
]

# Pre-compile
_COMPILED = [(re.compile(pat, re.IGNORECASE), tool, fn) for pat, tool, fn in _RULES]


class AutomationRouter:
    """
    Routes natural-language input to automation tools without calling the LLM.

    Returns (tool_name, args_dict) on match, or (None, None) on miss.
    """

    def __init__(self, registry):
        self.registry = registry

    def route(self, text: str) -> Optional[ToolResult]:
        """
        Try to match text to an automation rule.
        Returns ToolResult if matched and executed, None if no match (→ falls to LLM).
        """
        stripped = text.strip()
        for pattern, tool_name, arg_fn in _COMPILED:
            m = pattern.match(stripped)
            if m:
                args = arg_fn(m)
                logger.info(f"AutomationRouter matched: {tool_name!r} args={args}")
                result = self.registry.execute(tool_name, args)
                if result is not None:
                    return result
        return None

    def route_slash(self, cmd: str, arg: str) -> Optional[ToolResult]:
        """
        Handle explicit slash-command automation calls.
        /open, /close, /volume, /search, /type, /file, /screenshot, /apps
        """
        cmd = cmd.lstrip("/").lower()
        dispatch = {
            "open":       ("app_launcher",   {"action": "open",  "app": arg}),
            "close":      ("app_launcher",   {"action": "close", "app": arg}),
            "apps":       ("app_launcher",   {"action": "list"}),
            "volume":     ("system_control", _volume_arg_from_str(arg)),
            "mute":       ("system_control", {"action": "mute"}),
            "shutdown":   ("system_control", {"action": "shutdown"}),
            "restart":    ("system_control", {"action": "restart"}),
            "sleep":      ("system_control", {"action": "sleep"}),
            "lock":       ("system_control", {"action": "lock"}),
            "search":     ("web_search",     {"query": arg, "engine": "duckduckgo"}),
            "youtube":    ("web_search",     {"query": arg, "engine": "youtube"}),
            "url":        ("web_search",     {"url": arg}),
            "copy":       ("clipboard",      {"action": "write", "text": arg}),
            "paste":      ("clipboard",      {"action": "read"}),
            "clipboard":  ("clipboard",      {"action": "read"}),
            "type":       ("keyboard",       {"action": "type", "text": arg}),
            "hotkey":     ("keyboard",       {"action": "hotkey", "keys": arg}),
            "screenshot": ("keyboard",       {"action": "screenshot"}),
            "file":       ("file_ops",       {"action": "open", "path": arg}),
            "ls":         ("file_ops",       {"action": "list", "path": arg or "."}),
        }
        if cmd not in dispatch:
            return None
        tool_name, args = dispatch[cmd]
        logger.info(f"Slash cmd /{cmd} -> {tool_name} args={args}")
        return self.registry.execute(tool_name, args)


def _volume_arg_from_str(arg: str) -> dict:
    arg = arg.strip().lower().rstrip("%")
    if arg.isdigit():
        return {"action": "set", "level": int(arg)}
    return {"action": arg or "get"}
