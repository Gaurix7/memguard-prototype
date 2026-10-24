import sqlite3
from datetime import datetime

DB_FILE = "memguard.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memory_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            source_agent TEXT NOT NULL,
            source_trust TEXT NOT NULL,
            origin_document TEXT,
            sim_day INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print("Database ready.")

def add_memory(content, source_agent, source_trust, origin_document=None, sim_day=0):
    conn = get_connection()
    conn.execute(
        "INSERT INTO memory_entries (content, source_agent, source_trust, origin_document, sim_day, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (content, source_agent, source_trust, origin_document, sim_day, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_all_memories():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM memory_entries ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]

if __name__ == "__main__":
    init_db()