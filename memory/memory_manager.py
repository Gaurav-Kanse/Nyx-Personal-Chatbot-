"""
memory/memory_manager.py
High-level CRUD layer that wraps NyxDatabase for all persistent memory operations.
This is the single entry point for all read/write access to nyx.db.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from memory.database import NyxDatabase
from memory.models import ProfileEntry, Message, Note, AppRecord
from utils.logger import setup_logger

logger = setup_logger(__name__)


class MemoryManager:
    """
    Provides typed CRUD methods for all Nyx memory tables.

    Usage (from assistant.py):
        mm = MemoryManager()
        mm.set_profile("user_name", "Alice")
        name = mm.get_profile("user_name")
    """

    def __init__(self):
        self.db = NyxDatabase()
        self.session_id: str = str(uuid.uuid4())
        logger.info(f"MemoryManager online — session {self.session_id[:8]}…")

    # ------------------------------------------------------------------ #
    # USER PROFILE                                                         #
    # ------------------------------------------------------------------ #

    def get_profile(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve a single profile value by key."""
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT value FROM user_profile WHERE key = ?", (key,)
            ).fetchone()
        return row["value"] if row else default

    def set_profile(self, key: str, value: str) -> None:
        """Insert or update a profile key-value pair."""
        now = datetime.now().isoformat()
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO user_profile (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                """,
                (key, value, now),
            )
            conn.commit()
        logger.debug(f"Profile updated: {key} = {value!r}")

    def get_all_profile(self) -> Dict[str, str]:
        """Return the complete user profile as a plain dict."""
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT key, value FROM user_profile").fetchall()
        return {row["key"]: row["value"] for row in rows}

    def delete_profile(self, key: str) -> None:
        """Remove a profile key."""
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM user_profile WHERE key = ?", (key,))
            conn.commit()

    # ------------------------------------------------------------------ #
    # CONVERSATION HISTORY                                                 #
    # ------------------------------------------------------------------ #

    def log_message(self, role: str, content: str) -> Message:
        """Persist a single chat turn to the DB and return a Message object."""
        msg = Message(role=role, content=content, session_id=self.session_id)
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO conversation_history (session_id, timestamp, role, content)
                VALUES (?, ?, ?, ?)
                """,
                (msg.session_id, msg.timestamp, msg.role, msg.content),
            )
            conn.commit()
            msg.id = cursor.lastrowid
        return msg

    def get_recent_messages(self, limit: int = 20) -> List[Message]:
        """Fetch the N most recent messages across all sessions (for context injection)."""
        with self.db.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, session_id, timestamp, role, content
                FROM conversation_history
                ORDER BY id DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        # Reverse so oldest first (chronological order for LLM context)
        return [
            Message(
                id=r["id"],
                session_id=r["session_id"],
                timestamp=r["timestamp"],
                role=r["role"],
                content=r["content"],
            )
            for r in reversed(rows)
        ]

    def get_session_messages(self) -> List[Message]:
        """Fetch all messages from the current session."""
        with self.db.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, session_id, timestamp, role, content
                FROM conversation_history
                WHERE session_id = ?
                ORDER BY id ASC
                """,
                (self.session_id,),
            ).fetchall()
        return [
            Message(
                id=r["id"],
                session_id=r["session_id"],
                timestamp=r["timestamp"],
                role=r["role"],
                content=r["content"],
            )
            for r in rows
        ]

    def clear_old_history(self, keep_last: int = 200) -> None:
        """Prune conversation history, keeping only the N most recent rows."""
        with self.db.get_connection() as conn:
            conn.execute(
                """
                DELETE FROM conversation_history
                WHERE id NOT IN (
                    SELECT id FROM conversation_history ORDER BY id DESC LIMIT ?
                )
                """,
                (keep_last,),
            )
            conn.commit()
        logger.info(f"Pruned conversation history to last {keep_last} messages.")

    # ------------------------------------------------------------------ #
    # NOTES                                                                #
    # ------------------------------------------------------------------ #

    def add_note(self, title: str, content: str, category: str = "general") -> Note:
        """Create a new note and return it with its assigned ID."""
        now = datetime.now().isoformat()
        note = Note(title=title, content=content, category=category,
                    created_at=now, updated_at=now)
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO notes (title, content, category, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (note.title, note.content, note.category, note.created_at, note.updated_at),
            )
            conn.commit()
            note.id = cursor.lastrowid
        logger.info(f"Note added: [{note.id}] {note.title!r}")
        return note

    def get_notes(self, category: Optional[str] = None) -> List[Note]:
        """Retrieve all notes, optionally filtered by category."""
        with self.db.get_connection() as conn:
            if category:
                rows = conn.execute(
                    "SELECT * FROM notes WHERE category = ? ORDER BY updated_at DESC",
                    (category,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM notes ORDER BY updated_at DESC"
                ).fetchall()
        return [
            Note(
                id=r["id"],
                title=r["title"],
                content=r["content"],
                category=r["category"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
            for r in rows
        ]

    def update_note(self, note_id: int, content: str) -> bool:
        """Update the content of an existing note by ID. Returns True if found."""
        now = datetime.now().isoformat()
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE notes SET content = ?, updated_at = ? WHERE id = ?",
                (content, now, note_id),
            )
            conn.commit()
        updated = cursor.rowcount > 0
        if updated:
            logger.info(f"Note {note_id} updated.")
        return updated

    def delete_note(self, note_id: int) -> bool:
        """Delete a note by ID. Returns True if it existed."""
        with self.db.get_connection() as conn:
            cursor = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            conn.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Note {note_id} deleted.")
        return deleted

    # ------------------------------------------------------------------ #
    # APP USAGE TRACKING                                                   #
    # ------------------------------------------------------------------ #

    def record_app_launch(self, name: str, path: str) -> AppRecord:
        """Track or increment usage count for a launched application."""
        now = datetime.now().isoformat()
        with self.db.get_connection() as conn:
            existing = conn.execute(
                "SELECT use_count FROM app_usage WHERE name = ?", (name,)
            ).fetchone()
            if existing:
                new_count = existing["use_count"] + 1
                conn.execute(
                    "UPDATE app_usage SET use_count = ?, last_used = ? WHERE name = ?",
                    (new_count, now, name),
                )
            else:
                new_count = 1
                conn.execute(
                    "INSERT INTO app_usage (name, path, use_count, last_used) VALUES (?, ?, ?, ?)",
                    (name, path, new_count, now),
                )
            conn.commit()
        return AppRecord(name=name, path=path, last_used=now, use_count=new_count)

    def get_frequent_apps(self, limit: int = 10) -> List[AppRecord]:
        """Return the most frequently launched apps."""
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM app_usage ORDER BY use_count DESC LIMIT ?", (limit,)
            ).fetchall()
        return [
            AppRecord(
                name=r["name"],
                path=r["path"],
                last_used=r["last_used"],
                use_count=r["use_count"],
            )
            for r in rows
        ]

    # ------------------------------------------------------------------ #
    # CONTEXT BUILDER (for system prompt injection)                        #
    # ------------------------------------------------------------------ #

    def build_memory_context(self) -> str:
        """
        Construct a concise memory block to prepend to the system prompt.
        Keeps token count low while giving Nyx useful persistent context.
        """
        lines: List[str] = []

        # -- User profile --
        profile = self.get_all_profile()
        if profile:
            lines.append("## About the User")
            for k, v in profile.items():
                lines.append(f"- {k.replace('_', ' ').title()}: {v}")

        # -- Recent notes (max 5, truncated) --
        notes = self.get_notes()[:5]
        if notes:
            lines.append("\n## User Notes")
            for note in notes:
                snippet = note.content[:120].replace("\n", " ")
                lines.append(f"- [{note.category}] **{note.title}**: {snippet}…")

        # -- Frequent apps --
        apps = self.get_frequent_apps(5)
        if apps:
            lines.append("\n## Frequently Used Apps")
            lines.append(", ".join(a.name for a in apps))

        return "\n".join(lines) if lines else ""
