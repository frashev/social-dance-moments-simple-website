from pathlib import Path
import sqlite3
from contextlib import contextmanager
from typing import Generator

DB_PATH = Path(__file__).parent.parent / "dance_app.db"

def init_db() -> None:
    """Initialize SQLite database with schema."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT,
        is_admin INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS songs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        image_path TEXT,
        created_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS workshops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT NOT NULL,
        location TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        style TEXT NOT NULL,
        difficulty TEXT DEFAULT 'intermediate',
        instructor_name TEXT,
        description TEXT,
        max_participants INTEGER DEFAULT 0,
        lat REAL,
        lon REAL,
        cards TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        workshop_id INTEGER NOT NULL,
        registered_at TEXT NOT NULL,
        attended INTEGER DEFAULT 0,
        notify_enabled INTEGER DEFAULT 1,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(workshop_id) REFERENCES workshops(id),
        UNIQUE(user_id, workshop_id)
    )''')
    conn.commit()
    conn.close()

@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

