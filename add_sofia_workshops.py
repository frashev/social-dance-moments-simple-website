import sqlite3
from datetime import datetime, timedelta
from app.database import DB_PATH


def add_sofia_workshops():
    """Add 20 sample workshops in Sofia."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    workshops = [
        # Salsa (5)
        ("Sofia", "Studio Ritmo", "2026-02-15", "19:00", "salsa", "beginner", "Maria", "Salsa basics for beginners"),
        ("Sofia", "Dance Zone", "2026-02-16", "20:00", "salsa", "intermediate", "Carlos",
         "Intermediate salsa patterns"),
        ("Sofia", "Rhythm Hall", "2026-02-20", "19:30", "salsa", "advanced", "Juan", "Advanced salsa techniques"),
        ("Sofia", "Studio Ritmo", "2026-02-22", "18:00", "salsa", "beginner", "Maria", "Salsa for complete beginners"),
        ("Sofia", "Dance Zone", "2026-02-28", "20:30", "salsa", "intermediate", "Carlos", "Partner work in salsa"),

        # Bachata (5)
        ("Sofia", "Studio Bachata", "2026-02-17", "20:00", "bachata", "beginner", "Diego", "Bachata romance basics"),
        ("Sofia", "Tropical Nights", "2026-02-18", "19:00", "bachata", "intermediate", "Sofia",
         "Bachata sensual movements"),
        ("Sofia", "Studio Bachata", "2026-02-24", "20:30", "bachata", "advanced", "Diego", "Advanced bachata styling"),
        ("Sofia", "Tropical Nights", "2026-02-25", "19:30", "bachata", "beginner", "Sofia", "Bachata for couples"),
        ("Sofia", "Dance Zone", "2026-03-02", "20:00", "bachata", "intermediate", "Diego", "Bachata turns and spins"),

        # Zouk (5)
        ("Sofia", "Zouk Paradise", "2026-02-19", "19:00", "zouk", "beginner", "Lena", "Introduction to zouk"),
        ("Sofia", "Latin Heat", "2026-02-21", "20:00", "zouk", "intermediate", "Bruno", "Zouk connection and leads"),
        ("Sofia", "Zouk Paradise", "2026-02-26", "19:30", "zouk", "advanced", "Lena", "Advanced zouk choreography"),
        ("Sofia", "Latin Heat", "2026-03-01", "20:30", "zouk", "beginner", "Bruno", "Zouk fundamentals"),
        ("Sofia", "Zouk Paradise", "2026-03-03", "18:00", "zouk", "intermediate", "Lena", "Zouk styling and flow"),

        # Kizomba (5)
        ("Sofia", "Kizomba Club", "2026-02-23", "21:00", "kizomba", "beginner", "Andre", "Kizomba basics and steps"),
        ("Sofia", "African Rhythm", "2026-02-27", "20:00", "kizomba", "intermediate", "Yara", "Kizomba connection"),
        ("Sofia", "Kizomba Club", "2026-03-04", "21:00", "kizomba", "advanced", "Andre", "Advanced kizomba moves"),
        ("Sofia", "African Rhythm", "2026-03-05", "20:30", "kizomba", "beginner", "Yara", "Kizomba for beginners"),
        ("Sofia", "Kizomba Club", "2026-03-06", "21:30", "kizomba", "intermediate", "Andre",
         "Kizomba partner dynamics"),
    ]

    for city, location, date, time, style, difficulty, instructor, desc in workshops:
        c.execute(
            "INSERT INTO workshops (city, location, date, time, style, difficulty, instructor_name, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (city, location, date, time, style, difficulty, instructor, desc)
        )

    conn.commit()
    conn.close()
    print("✅ Added 20 workshops to Sofia!")


if __name__ == "__main__":
    add_sofia_workshops()