#!/usr/bin/env python3
"""
🔧 Reset: Set all workshops to their predefined_locations base coordinates
This ensures the migration script will work from the correct starting point
"""

import sqlite3
from collections import defaultdict
from app.database import DB_PATH

def reset_to_predefined_coordinates():
    """Reset all workshop coordinates to their predefined_locations base."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Fetch all workshops
    c.execute("""
        SELECT id, city, location
        FROM workshops
        WHERE lat IS NOT NULL AND lon IS NOT NULL
    """)
    workshops = c.fetchall()

    print("🚀 Resetting workshop coordinates to predefined_locations base...\n")

    reset_count = 0
    skipped_count = 0

    for w in workshops:
        workshop_id = w['id']
        city = w['city']
        location = w['location']

        # Look up in predefined_locations
        c.execute(
            "SELECT lat, lon FROM predefined_locations WHERE location_name = ? AND city = ?",
            (location, city)
        )
        result = c.fetchone()

        if result:
            base_lat = result['lat']
            base_lon = result['lon']

            # Update workshop with base coordinates
            c.execute(
                "UPDATE workshops SET lat = ?, lon = ? WHERE id = ?",
                (base_lat, base_lon, workshop_id)
            )
            reset_count += 1
            print(f"✅ Workshop {workshop_id}: Reset to ({base_lat}, {base_lon})")
        else:
            skipped_count += 1
            print(f"⏭️  Workshop {workshop_id}: No predefined location found for '{location}', {city}")

    conn.commit()
    conn.close()

    print(f"\n📊 Summary:")
    print(f"   ✅ Reset: {reset_count}")
    print(f"   ⏭️  Skipped: {skipped_count}")
    print(f"\n✨ All workshops reset to predefined base coordinates!")
    print(f"Now you can safely run: python migrate_collision_avoidance.py\n")


if __name__ == "__main__":
    reset_to_predefined_coordinates()

