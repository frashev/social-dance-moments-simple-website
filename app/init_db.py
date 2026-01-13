from pathlib import Path
import sqlite3

def init_db(db_path: Path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS songs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        image_path TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS workshops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        city TEXT,
        location TEXT,
        date TEXT,
        time TEXT,
        style TEXT,
        difficulty TEXT,
        instructor_name TEXT,
        description TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    db_file = Path(__file__).parent.parent / "db.sqlite3"
    init_db(db_file)
    print(f"Initialized DB at {db_file}")

