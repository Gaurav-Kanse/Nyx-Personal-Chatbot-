"""
scratch/test_memory.py
Phase 2 verification script -- exercises MemoryManager and NyxBrain end-to-end.
Run from the project root:
    python scratch/test_memory.py
"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from memory.memory_manager import MemoryManager
from core.brain import NyxBrain

PASS = "[PASS]"
FAIL = "[FAIL]"


def section(title: str):
    print(f"\n{'─'*50}")
    print(f"  {title}")
    print(f"{'─'*50}")


def check(label: str, condition: bool):
    print(f"  {PASS if condition else FAIL}  {label}")
    return condition


def test_profile(mm: MemoryManager):
    section("1. User Profile CRUD")
    mm.set_profile("user_name", "Alice")
    check("set_profile stores value",  mm.get_profile("user_name") == "Alice")

    mm.set_profile("user_name", "Bob")
    check("set_profile updates value", mm.get_profile("user_name") == "Bob")

    mm.set_profile("favorite_color", "indigo")
    profile = mm.get_all_profile()
    check("get_all_profile returns dict",  isinstance(profile, dict))
    check("get_all_profile has two keys", len(profile) >= 2)

    mm.delete_profile("favorite_color")
    check("delete_profile removes key", mm.get_profile("favorite_color") is None)


def test_messages(mm: MemoryManager):
    section("2. Conversation History")
    msg1 = mm.log_message("user", "Hello Nyx!")
    msg2 = mm.log_message("assistant", "Hello, I'm here to help.")
    check("log_message returns Message with id",  msg1.id is not None)
    check("log_message assigns session_id", msg1.session_id == mm.session_id)

    recent = mm.get_recent_messages(10)
    check("get_recent_messages returns list", isinstance(recent, list))
    check("recent messages non-empty",  len(recent) >= 2)

    session_msgs = mm.get_session_messages()
    check("get_session_messages for current session", len(session_msgs) >= 2)
    check("messages ordered oldest first", session_msgs[0].id <= session_msgs[-1].id)


def test_notes(mm: MemoryManager):
    section("3. Notes CRUD")
    note = mm.add_note("Project Ideas", "Build a local AI assistant.", "dev")
    check("add_note returns Note with id",  note.id is not None)

    notes = mm.get_notes()
    check("get_notes returns list",  len(notes) >= 1)

    filtered = mm.get_notes(category="dev")
    check("get_notes with category filter",  all(n.category == "dev" for n in filtered))

    updated = mm.update_note(note.id, "Updated content here.")
    check("update_note returns True on success", updated is True)

    deleted = mm.delete_note(note.id)
    check("delete_note returns True on success",  deleted is True)

    gone = mm.get_notes()
    check("deleted note not in list", all(n.id != note.id for n in gone))


def test_apps(mm: MemoryManager):
    section("4. App Usage Tracking")
    rec1 = mm.record_app_launch("Notepad", "C:\\Windows\\notepad.exe")
    check("record_app_launch use_count starts at 1", rec1.use_count == 1)

    rec2 = mm.record_app_launch("Notepad", "C:\\Windows\\notepad.exe")
    check("record_app_launch increments count", rec2.use_count == 2)

    apps = mm.get_frequent_apps(5)
    check("get_frequent_apps returns list",  isinstance(apps, list))
    check("Notepad in frequent apps",  any(a.name == "Notepad" for a in apps))


def test_context(mm: MemoryManager):
    section("5. Memory Context Builder")
    mm.set_profile("user_name", "TestUser")
    mm.add_note("Quick Thought", "Check context builder.", "test")
    ctx = mm.build_memory_context()
    check("build_memory_context returns non-empty string", bool(ctx))
    check("context includes user name", "TestUser" in ctx)
    print(f"\n  Context preview:\n{ctx[:300]}\n")


def test_brain():
    section("6. NyxBrain Integration")
    brain = NyxBrain()
    brain.set_user_name("BrainUser")
    check("set_user_name persists via get_user_name", brain.get_user_name() == "BrainUser")

    brain.log_user_message("Testing brain.")
    brain.log_assistant_message("Roger that.")

    note = brain.add_note("Brain Test", "NyxBrain note creation works.", "test")
    check("brain.add_note works",  note.id is not None)

    notes = brain.get_notes()
    check("brain.get_notes returns list",  len(notes) >= 1)

    ctx = brain.build_memory_context()
    check("brain.build_memory_context non-empty", bool(ctx))

    status = brain.get_status_info()
    check("get_status_info has user key", "user" in status)


def main():
    print("\n=== Nyx Phase 2 -- Memory System Verification ===\n")

    mm = MemoryManager()

    all_passed = True
    for test in [
        lambda: test_profile(mm),
        lambda: test_messages(mm),
        lambda: test_notes(mm),
        lambda: test_apps(mm),
        lambda: test_context(mm),
        test_brain,
    ]:
        try:
            test()
        except Exception as e:
            print(f"  {FAIL}  Exception: {e}")
            all_passed = False

    print(f"\n{'═'*50}")
    if all_passed:
        print("  [OK] All Phase 2 memory tests passed!")
    else:
        print("  [!!] Some tests failed -- check output above.")
    print(f"{'═'*50}\n")


if __name__ == "__main__":
    main()
