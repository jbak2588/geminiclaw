import os
import json
import sqlite3
from typing import List, Dict, Any

# Ensure storage directory exists
STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)

class SessionMemoryStore:
    """
    A persistent memory store for the Base Assistant (Pi Node) sessions,
    allowing 1:1 chats to continue across disconnects.
    """
    def __init__(self, db_path: str = os.path.join(STORAGE_DIR, "sessions.db")):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_messages (
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def add_message(self, session_id: str, role: str, content: str):
        """Add a single message to a session's history."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO session_messages (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content)
            )
            conn.commit()

    def get_session_history(self, session_id: str, limit: int = 50) -> List[Dict[str, str]]:
        """Retrieve the conversational history for a given session."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Order by timestamp ASC
            cursor.execute(
                "SELECT role, content FROM session_messages WHERE session_id = ? ORDER BY timestamp ASC LIMIT ?",
                (session_id, limit)
            )
            rows = cursor.fetchall()
            return [{"role": row[0], "content": row[1]} for row in rows]

    def clear_session(self, session_id: str):
        """Clear all messages for a specific session."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM session_messages WHERE session_id = ?", (session_id,))
            conn.commit()

    def compact_session(self, session_id: str, summary: str):
        """Replace all session messages with a single compressed summary.
        
        This deletes the existing conversation and stores the summary
        as a 'system' role message, which the Pi Agent interprets as
        prior context.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Count messages before deletion for reporting
            cursor.execute(
                "SELECT COUNT(*) FROM session_messages WHERE session_id = ?",
                (session_id,)
            )
            count = cursor.fetchone()[0]
            # Delete all existing messages
            cursor.execute("DELETE FROM session_messages WHERE session_id = ?", (session_id,))
            # Insert summary as a system message
            cursor.execute(
                "INSERT INTO session_messages (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, "system", summary)
            )
            conn.commit()
            return count

    def get_message_count(self, session_id: str) -> int:
        """Return the number of messages in a session."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM session_messages WHERE session_id = ?",
                (session_id,)
            )
            return cursor.fetchone()[0]

# Global instance
memory_store = SessionMemoryStore()
