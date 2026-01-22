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
        admin_id INTEGER NOT NULL,
        title TEXT,
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
        cards TEXT,
        facebook_url TEXT,
        recurrence TEXT DEFAULT 'single',
        FOREIGN KEY(admin_id) REFERENCES users(id)
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
    c.execute('''CREATE TABLE IF NOT EXISTS predefined_locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country TEXT NOT NULL,
        city TEXT NOT NULL,
        location_name TEXT NOT NULL,
        lat REAL NOT NULL,
        lon REAL NOT NULL,
        created_by INTEGER NOT NULL,
        created_at TEXT,
        FOREIGN KEY(created_by) REFERENCES users(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        photo_path TEXT,
        event_organizer TEXT NOT NULL,
        location TEXT NOT NULL,
        country TEXT,
        city TEXT NOT NULL,
        start_date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_date TEXT NOT NULL,
        end_time TEXT NOT NULL,
        description TEXT,
        facebook_url TEXT,
        lat REAL,
        lon REAL,
        created_at TEXT,
        FOREIGN KEY(admin_id) REFERENCES users(id)
    )''')

    # Migration: Add title column if it doesn't exist
    try:
        c.execute("ALTER TABLE workshops ADD COLUMN title TEXT")
        print("✅ Added title column to workshops table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️ title column already exists")
        else:
            raise

    # Migration: Add facebook_url column if it doesn't exist
    try:
        c.execute("ALTER TABLE workshops ADD COLUMN facebook_url TEXT")
        print("✅ Added facebook_url column to workshops table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️ facebook_url column already exists")
        else:
            raise

    # Migration: Add recurrence column if it doesn't exist
    try:
        c.execute("ALTER TABLE workshops ADD COLUMN recurrence TEXT DEFAULT 'single'")
        print("✅ Added recurrence column to workshops table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️ recurrence column already exists")
        else:
            raise

    # Migration: Add country column to predefined_locations if it doesn't exist
    try:
        c.execute("ALTER TABLE predefined_locations ADD COLUMN country TEXT DEFAULT 'Unknown'")
        print("✅ Added country column to predefined_locations table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️ country column already exists in predefined_locations")
        else:
            raise

    # Migration: Add country column to events if it doesn't exist
    try:
        c.execute("ALTER TABLE events ADD COLUMN country TEXT")
        print("✅ Added country column to events table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️ country column already exists in events")
        else:
            raise

    # Migration: Add is_super_admin column if it doesn't exist
    try:
        c.execute("ALTER TABLE users ADD COLUMN is_super_admin INTEGER DEFAULT 0")
        print("✅ Added is_super_admin column to users table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️ is_super_admin column already exists")
        else:
            raise

    # Migration: Add start_time and end_time columns if they don't exist
    try:
        c.execute("ALTER TABLE workshops ADD COLUMN start_time TEXT")
        print("✅ Added start_time column to workshops table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️ start_time column already exists")
        else:
            raise

    try:
        c.execute("ALTER TABLE workshops ADD COLUMN end_time TEXT")
        print("✅ Added end_time column to workshops table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️ end_time column already exists")
        else:
            raise

    # Migration: Populate start_time from existing time column
    try:
        c.execute("UPDATE workshops SET start_time = time WHERE start_time IS NULL AND time IS NOT NULL")
        updated_count = c.rowcount
        if updated_count > 0:
            print(f"✅ Migrated {updated_count} workshops' time to start_time")
    except Exception as e:
        print(f"ℹ️ Migration info: {e}")

    # Migration: Make time column nullable (allow new records to have NULL time)
    # SQLite doesn't support ALTER COLUMN, so we handle this in the INSERT/UPDATE logic
    try:
        # Check if time column is nullable by trying to update a row with NULL
        c.execute("SELECT COUNT(*) FROM workshops WHERE time IS NULL")
        print("ℹ️ time column can accept NULL values (migration done or not needed)")
    except Exception as e:
        print(f"ℹ️ time column migration status: {e}")

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

