"""
automation/tools/web_search.py
Open browser searches and URLs — no API key, no network calls from Nyx itself.
Uses the system's default browser via the webbrowser stdlib module.
"""

import webbrowser
import urllib.parse
from typing import Any, Dict

from automation.base import AutomationTool, ToolMeta, ToolResult
from utils.logger import setup_logger

logger = setup_logger(__name__)

_ENGINES = {
    "duckduckgo": "https://duckduckgo.com/?q={query}",
    "google":     "https://www.google.com/search?q={query}",
    "bing":       "https://www.bing.com/search?q={query}",
    "youtube":    "https://www.youtube.com/results?search_query={query}",
    "github":     "https://github.com/search?q={query}",
    "stackoverflow": "https://stackoverflow.com/search?q={query}",
    "wikipedia":  "https://en.wikipedia.org/wiki/Special:Search?search={query}",
    "reddit":     "https://www.reddit.com/search/?q={query}",
}


class WebSearchTool(AutomationTool):
    meta = ToolMeta(
        name="web_search",
        description="Open a web search or specific URL in the default browser.",
        aliases=["search", "browse", "google", "youtube"],
        examples=["search python tutorials", "youtube lo-fi music", "open https://github.com"],
    )

    def execute(self, args: Dict[str, Any]) -> ToolResult:
        # Direct URL
        if "url" in args:
            url = args["url"].strip()
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            webbrowser.open(url)
            logger.info(f"Opened URL: {url}")
            return ToolResult(True, f"Opening {url} in your browser.")

        # Search query
        query = args.get("query", "").strip()
        if not query:
            return ToolResult(False, "No search query provided.")

        engine = args.get("engine", "duckduckgo").lower()
        template = _ENGINES.get(engine, _ENGINES["duckduckgo"])
        encoded = urllib.parse.quote_plus(query)
        url = template.format(query=encoded)

        webbrowser.open(url)
        logger.info(f"Web search [{engine}]: {query!r} -> {url}")

        engine_display = engine.title()
        return ToolResult(True, f"Searching {engine_display} for: {query}")
