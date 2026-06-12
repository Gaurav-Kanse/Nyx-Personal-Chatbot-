"""
memory/models.py
Dataclass schemas for Nyx's persistent memory objects.
These are pure data containers — no DB logic lives here.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class ProfileEntry:
    """A single key-value pair from the user_profile table."""
    key: str
    value: str
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Message:
    """A single turn in a conversation session."""
    role: str           # "user" or "assistant"
    content: str
    session_id: str     # UUID of the conversation session
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    id: Optional[int] = None


@dataclass
class Note:
    """A user-created note with optional categorisation."""
    title: str
    content: str
    category: str = "general"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    id: Optional[int] = None


@dataclass
class AppRecord:
    """Tracks applications Nyx has launched for the user."""
    name: str
    path: str
    last_used: str = field(default_factory=lambda: datetime.now().isoformat())
    use_count: int = 1
