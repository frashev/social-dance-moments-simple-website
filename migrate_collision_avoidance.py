#!/usr/bin/env python3
"""
🔧 Migration script: Distribute workshops by style around each location
This script groups workshops by LOCATION and distributes different STYLES
in a circular pattern around the location's base coordinates.
All workshops at the same location get spread out by style, not date.
"""

import sqlite3
import math
from pathlib import Path

# Import from app module
from app.database import DB_PATH

# Style-based positions in circular pattern (0-360°)
# Each style gets a unique angle around the location
STYLE_ANGLES = {
    "salsa": 45,          # Northeast
    "bachata": 135,       # Northwest
    "kizomba": 225,       # Southwest
    "zouk": 315,          # Southeast
    "lets_party": 0,      # North
    # Add more styles as needed
}

def get_style_angle(style: str) -> float:
    """Get the angle for a style in circular distribution (0-360 degrees)."""
    if style in STYLE_ANGLES:
        return STYLE_ANGLES[style]
    # For unknown styles, assign evenly
    all_styles = list(STYLE_ANGLES.keys())
    if style not in all_styles:
        all_styles.append(style)
    return (len(all_styles) - 1) * (360 / len(all_styles))

def apply_circular_spread(base_lat: float, base_lon: float, style: str, style_index: int = 0, style_count: int = 1, radius: float = 0.000063) -> tuple:
    """
    Apply circular spreading around base coordinates based on style.
    Also adds small offset if multiple workshops of same style at same location.

    Args:
        base_lat, base_lon: Center coordinates (from predefined location)
        style: Dance style
        style_index: Index of this workshop within its style group (0, 1, 2...)
        style_count: Total workshops of this style at this location
        radius: Spread radius in degrees (~3 meters at equator)

    Returns:
        Tuple of (adjusted_lat, adjusted_lon)
    """
    angle_degrees = get_style_angle(style)
    # Compass bearing: 0°=N, 90°=E, 180°=S, 270°=W
    # Latitude increases North, Longitude increases East
    # So: N (0°) -> +lat, E (90°) -> +lon, S (180°) -> -lat, W (270°) -> -lon
    angle_radians = math.radians(angle_degrees)

    # Calculate offset using circular pattern
    # Use: lat = radius * cos(angle), lon = radius * sin(angle)
    # This correctly maps compass bearings to lat/lon space
    lat_offset = radius * math.cos(angle_radians)
    lon_offset = radius * math.sin(angle_radians)

    # If multiple workshops of same style, add small collision avoidance offset
    if style_count > 1:
        collision_radius = 0.000025  # Increased from 0.000015 for even better spacing between same-style workshops
        collision_angle_deg = (style_index * 360 / style_count)
        collision_angle = math.radians(collision_angle_deg)

        collision_lat_offset = collision_radius * math.cos(collision_angle)
        collision_lon_offset = collision_radius * math.sin(collision_angle)

        lat_offset += collision_lat_offset
        lon_offset += collision_lon_offset

    adjusted_lat = base_lat + lat_offset
    adjusted_lon = base_lon + lon_offset

    return (adjusted_lat, adjusted_lon)

def migrate_workshops():
    """Distribute all workshops by style around their location coordinates."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Fetch all workshops with location info
    c.execute("""
        SELECT id, lat, lon, style, city, location 
        FROM workshops 
        WHERE lat IS NOT NULL AND lon IS NOT NULL 
        ORDER BY location, style, id
    """)
    workshops = c.fetchall()

    if not workshops:
        print("ℹ️  No workshops found with coordinates. Exiting.")
        conn.close()
        return

    print(f"Found {len(workshops)} workshops to process.\n")

    # Group workshops by LOCATION to find base coordinates
    location_groups = {}

    for workshop in workshops:
        # Convert Row to dict for mutability
        ws_dict = dict(workshop)
        location_key = (ws_dict['city'], ws_dict['location'])
        if location_key not in location_groups:
            location_groups[location_key] = {
                'base_lat': ws_dict['lat'],
                'base_lon': ws_dict['lon'],
                'workshops': []
            }
        location_groups[location_key]['workshops'].append(ws_dict)

    # For each location, group workshops by style to track indices
    for location_key in location_groups:
        style_groups = {}
        for workshop in location_groups[location_key]['workshops']:
            style = workshop['style']
            if style not in style_groups:
                style_groups[style] = []
            style_groups[style].append(workshop)
        location_groups[location_key]['style_groups'] = style_groups

        # Add style indices to each workshop
        for workshop in location_groups[location_key]['workshops']:
            style = workshop['style']
            style_idx = style_groups[style].index(workshop)
            workshop['style_index'] = style_idx
            workshop['style_count'] = len(style_groups[style])

    updated_count = 0
    skipped_count = 0

    print("Distributing workshops by style around each location:\n")

    for location_key, location_data in location_groups.items():
        city, location = location_key
        base_lat = location_data['base_lat']
        base_lon = location_data['base_lon']
        workshops_at_location = location_data['workshops']

        print(f"Location: {location}, {city}")
        print(f"   Base coordinates: ({base_lat}, {base_lon})")
        print(f"   Workshops: {len(workshops_at_location)}\n")

        for workshop in workshops_at_location:
            workshop_id = workshop['id']
            original_lat = workshop['lat']
            original_lon = workshop['lon']
            style = workshop['style']
            style_index = workshop['style_index']
            style_count = workshop['style_count']

            try:
                # Apply circular spread based on style, with collision avoidance for same-style workshops
                new_lat, new_lon = apply_circular_spread(
                    base_lat, base_lon, style,
                    style_index=style_index,
                    style_count=style_count
                )

                # Update the workshop
                c.execute(
                    "UPDATE workshops SET lat = ?, lon = ? WHERE id = ?",
                    (new_lat, new_lon, workshop_id)
                )
                updated_count += 1
                angle = get_style_angle(style)
                style_pos = f"#{style_index + 1}/{style_count}" if style_count > 1 else ""
                print(f"   {style:12} (angle: {angle:3}) {style_pos:8}: ({original_lat:.6f}, {original_lon:.6f}) -> ({new_lat:.6f}, {new_lon:.6f})")

            except Exception as e:
                print(f"   ERROR Workshop {workshop_id} ({style}) - Error: {e}")

        print()

    conn.commit()
    conn.close()

    print(f"Migration complete!")
    print(f"   Updated: {updated_count}")
    print(f"   Total: {len(workshops)}")

if __name__ == "__main__":
    print("Starting collision avoidance migration...\n")
    migrate_workshops()
    print("Done!")

