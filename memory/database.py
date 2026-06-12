import sqlite3
import os
from pathlib import Path
from core.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class NyxDatabase:
    def __init__(self):
        self.db_path = Path(Config.BASE_DIR) / "data" / "nyx.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize_schema()

    def get_connection(self) -> sqlite3.Connection:
        """Returns a sqlite3 connection with dict-like row parsing."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_schema(self):
        """Creates the required tables if they do not exist."""
        queries = [
            # 1. User Profile Table
            """
            CREATE TABLE IF NOT EXISTS user_profile (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """,
            # 2. Conversation Logs Table
            """
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL
            );
            """,
            # 3. Notes Table
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """,
            # 4. Applications Tracker Table
            """
            CREATE TABLE IF NOT EXISTS app_usage (
                name TEXT PRIMARY KEY,
                path TEXT NOT NULL,
                use_count INTEGER DEFAULT 1,
                last_used TEXT NOT NULL
            );
            """
        ]

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                for query in queries:
                    cursor.execute(query)
                conn.commit()
            logger.info("NyxDatabase schema initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize database schema: {e}")
            raise e
