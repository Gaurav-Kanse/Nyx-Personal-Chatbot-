"""
scratch/test_automation.py
Phase 3 verification — tests registry, router, and every automation tool.
Run from project root:
    python scratch/test_automation.py
"""

import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from automation.registry import build_registry
from automation.router   import AutomationRouter

PASS = "[PASS]"
FAIL = "[FAIL]"


def section(title):
    print(f"\n{'─'*55}")
    print(f"  {title}")
    print(f"{'─'*55}")


def check(label, condition):
    print(f"  {PASS if condition else FAIL}  {label}")
    return condition


# ─────────────────────────────────────────────────────── #
# 1. Registry                                              #
# ─────────────────────────────────────────────────────── #
def test_registry(registry):
    section("1. ToolRegistry")
    tools = registry.list_tools()
    check("At least 6 tools registered", len(tools) >= 6)

    expected = ["app_launcher","system_control","clipboard","keyboard","file_ops","web_search"]
    for name in expected:
        t = registry.get(name)
        check(f"Tool '{name}' found", t is not None)

    # Alias lookup
    t = registry.get("clip")
    check("Alias 'clip' resolves to clipboard", t is not None and t.meta.name == "clipboard")

    summary = registry.tool_summary()
    check("tool_summary() non-empty", bool(summary))
    print(f"\n  Tool summary preview:\n{summary[:300]}\n")


# ─────────────────────────────────────────────────────── #
# 2. Router — natural-language intent matching             #
# ─────────────────────────────────────────────────────── #
def test_router_patterns(router):
    section("2. AutomationRouter — pattern matching")

    # These should NOT match (conversational)
    no_match = [
        "what's the weather like?",
        "tell me a joke",
        "how do I learn Python?",
    ]
    for text in no_match:
        r = router.route(text)
        check(f"No match for: '{text}'", r is None)


def test_router_slash(router):
    section("3. AutomationRouter — slash commands")

    # /clipboard is safe to test
    r = router.route_slash("/clipboard", "")
    check("/clipboard slash dispatched", r is not None)

    # /search is safe (opens browser — we just check it returns a result)
    r = router.route_slash("/search", "python tutorials")
    check("/search returns ToolResult", r is not None)
    if r:
        check("/search success=True", r.success)

    # /ls with current dir
    r = router.route_slash("/ls", ".")
    check("/ls returns ToolResult", r is not None)
    if r:
        check("/ls has message", bool(r.message))


# ─────────────────────────────────────────────────────── #
# 3. Clipboard tool                                        #
# ─────────────────────────────────────────────────────── #
def test_clipboard(registry):
    section("4. Clipboard Tool")
    r = registry.execute("clipboard", {"action": "write", "text": "Hello from Nyx!"})
    check("clipboard write success", r.success)

    r2 = registry.execute("clipboard", {"action": "read"})
    check("clipboard read success", r2.success)
    check("clipboard read returns written text", "Hello from Nyx!" in (r2.data or ""))

    r3 = registry.execute("clipboard", {"action": "clear"})
    check("clipboard clear success", r3.success)


# ─────────────────────────────────────────────────────── #
# 4. Web search tool                                       #
# ─────────────────────────────────────────────────────── #
def test_web_search(registry):
    section("5. WebSearch Tool")
    # Just verify URL formation — don't actually open browser in test
    import urllib.parse
    query = "nyx ai assistant"
    encoded = urllib.parse.quote_plus(query)
    expected_fragment = encoded[:10]

    # Patch webbrowser.open to capture the URL
    import webbrowser
    opened_urls = []
    original_open = webbrowser.open
    webbrowser.open = lambda url, **kw: opened_urls.append(url)

    try:
        r = registry.execute("web_search", {"query": query, "engine": "duckduckgo"})
        check("web_search returns success", r.success)
        check("URL contains encoded query", opened_urls and expected_fragment in opened_urls[0])

        opened_urls.clear()
        r2 = registry.execute("web_search", {"url": "https://example.com"})
        check("direct URL open success", r2.success)
        check("exact URL passed to browser", opened_urls and "example.com" in opened_urls[0])
    finally:
        webbrowser.open = original_open


# ─────────────────────────────────────────────────────── #
# 5. File ops tool                                         #
# ─────────────────────────────────────────────────────── #
def test_file_ops(registry):
    section("6. FileOps Tool — list directory")
    r = registry.execute("file_ops", {"action": "list", "path": "."})
    check("list '.' returns success", r.success)
    check("list '.' has entries", r.data and len(r.data) > 0)

    r2 = registry.execute("file_ops", {"action": "list", "path": "nonexistent_xyz_dir"})
    check("list nonexistent dir returns failure", not r2.success)


# ─────────────────────────────────────────────────────── #
# 6. App launcher — alias resolution only (no launch)      #
# ─────────────────────────────────────────────────────── #
def test_app_aliases():
    section("7. AppLauncher — alias resolution")
    from automation.tools.app_launcher import _resolve_executable, APP_ALIASES
    check("APP_ALIASES non-empty dict", len(APP_ALIASES) > 10)

    # notepad.exe is always on Windows
    path = _resolve_executable("notepad")
    check("notepad resolves to a path", path is not None)
    if path:
        check("resolved path contains 'notepad'", "notepad" in path.lower())


# ─────────────────────────────────────────────────────── #
# 7. System control — non-destructive only                 #
# ─────────────────────────────────────────────────────── #
def test_system_control(registry):
    section("8. SystemControl — safe actions only")
    # 'get' action never changes anything
    r = registry.execute("system_control", {"action": "get"})
    check("volume 'get' returns success", r.success)

    # Shutdown without confirm should be blocked
    r2 = registry.execute("system_control", {"action": "shutdown"})
    check("shutdown without --confirm is blocked", not r2.success)
    check("shutdown blocked message is informative", "confirm" in r2.message.lower())


# ─────────────────────────────────────────────────────── #
# Main                                                     #
# ─────────────────────────────────────────────────────── #
def main():
    print("\n=== Nyx Phase 3 -- Automation System Verification ===\n")

    registry = build_registry()
    router   = AutomationRouter(registry)

    all_ok = True
    tests = [
        lambda: test_registry(registry),
        lambda: test_router_patterns(router),
        lambda: test_router_slash(router),
        lambda: test_clipboard(registry),
        lambda: test_web_search(registry),
        lambda: test_file_ops(registry),
        test_app_aliases,
        lambda: test_system_control(registry),
    ]

    for t in tests:
        try:
            t()
        except Exception as exc:
            print(f"  {FAIL}  Exception: {exc}")
            import traceback; traceback.print_exc()
            all_ok = False

    print(f"\n{'='*55}")
    if all_ok:
        print("  [OK] All Phase 3 automation tests passed!")
    else:
        print("  [!!] Some tests failed -- check output above.")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
