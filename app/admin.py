from fastapi import APIRouter, Form, HTTPException, Depends, Query
from .database import get_db
from .utils import verify_token, verify_token_with_refresh
from datetime import datetime
from fastapi import APIRouter, Form, Query, HTTPException

router = APIRouter(prefix="/admin", tags=["admin"])

import math

# Style angles for circular distribution (0°=N, 45°=NE, 90°=E, 135°=SE, 180°=S, 225°=SW, 270°=W, 315°=NW)
STYLE_ANGLES = {
    "salsa": 45,        # Northeast
    "bachata": 135,     # Southeast
    "kizomba": 225,     # Southwest
    "zouk": 315,        # Northwest
    "lets_party": 0,    # North
}

def get_style_angle(style: str) -> float:
    """Get the compass angle for a style."""
    return STYLE_ANGLES.get(style, 0)

def apply_style_deviation(lat: float, lon: float, style: str) -> tuple:
    """
    Apply small coordinate deviation based on dance style using circular distribution.
    This spreads markers on the map so they don't overlap.

    Args:
        lat: Base latitude
        lon: Base longitude
        style: Dance style (salsa, bachata, kizomba, zouk, lets_party)

    Returns:
        Tuple of (adjusted_lat, adjusted_lon)
    """
    angle_degrees = get_style_angle(style)
    angle_radians = math.radians(angle_degrees)

    # Use circular pattern: radius * cos(angle) for lat, radius * sin(angle) for lon
    # This correctly maps compass bearings (0°=N, 90°=E, 180°=S, 270°=W) to lat/lon space
    radius = 0.000063  # ~7 meters at equator

    lat_offset = radius * math.cos(angle_radians)
    lon_offset = radius * math.sin(angle_radians)

    adjusted_lat = lat + lat_offset
    adjusted_lon = lon + lon_offset

    print(f"Applied {style} circular distribution ({angle_degrees}°): ({lat}, {lon}) → ({adjusted_lat}, {adjusted_lon})")
    return (adjusted_lat, adjusted_lon)

def apply_collision_avoidance_deviation(lat: float, lon: float, city: str, location: str, style: str, style_index: int = 0, exclude_workshop_id: int = None) -> tuple:
    """
    Check if other workshops of the same style exist at the same location.
    If yes, apply additional small deviation within the style sector to avoid overlap.
    Uses deterministic circular positioning.

    Args:
        lat: Current latitude (after style deviation)
        lon: Current longitude (after style deviation)
        city: Workshop city
        location: Workshop location name
        style: Dance style
        style_index: Index of this workshop within its style group at this location
        exclude_workshop_id: Workshop ID to exclude from count (for updates)

    Returns:
        Tuple of (adjusted_lat, adjusted_lon)
    """
    with get_db() as conn:
        c = conn.cursor()

        # Count other workshops of same style at same location
        if exclude_workshop_id:
            c.execute(
                "SELECT COUNT(*) FROM workshops WHERE city = ? AND location = ? AND style = ? AND id != ?",
                (city, location, style, exclude_workshop_id)
            )
        else:
            c.execute(
                "SELECT COUNT(*) FROM workshops WHERE city = ? AND location = ? AND style = ?",
                (city, location, style)
            )

        style_count = c.fetchone()[0] + 1  # +1 to include current workshop

    if style_count > 1:
        # Apply collision avoidance within the style sector
        collision_radius = 0.000025  # ~2-3 meters for same-style spread
        collision_angle_deg = (style_index * 360 / style_count)
        collision_angle_rad = math.radians(collision_angle_deg)

        collision_lat_offset = collision_radius * math.cos(collision_angle_rad)
        collision_lon_offset = collision_radius * math.sin(collision_angle_rad)

        adjusted_lat = lat + collision_lat_offset
        adjusted_lon = lon + collision_lon_offset

        print(f"Collision avoidance (same {style}, #{style_index + 1}/{style_count}): ({lat}, {lon}) → ({adjusted_lat}, {adjusted_lon})")
        return (adjusted_lat, adjusted_lon)

    return (lat, lon)

def verify_admin(token: str = Query(...)) -> dict:
    """Verify that user is admin. Attempts to refresh if token is expired."""
    # First try normal verification
    payload = verify_token(token)
    if payload and payload.get("is_admin"):
        return payload

    # If normal verification failed, try with refresh
    payload, new_token = verify_token_with_refresh(token)
    if not payload or not payload.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Return payload with new_token info if refreshed
    payload["new_token"] = new_token  # Will be None if not refreshed
    return payload

def verify_super_admin(token: str = Query(...)) -> dict:
    """Verify that user is super_admin. Attempts to refresh if token is expired."""
    with get_db() as conn:
        c = conn.cursor()

        # First try normal verification
        payload = verify_token(token)
        if payload:
            user_id = payload.get("user_id")
            c.execute("SELECT is_super_admin FROM users WHERE id = ?", (user_id,))
            user = c.fetchone()
            if user and user['is_super_admin']:
                return payload

        # If normal verification failed, try with refresh
        payload, new_token = verify_token_with_refresh(token)
        if not payload:
            raise HTTPException(status_code=403, detail="Super admin access required")

        user_id = payload.get("user_id")
        c.execute("SELECT is_super_admin FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()

        if not user or not user['is_super_admin']:
            raise HTTPException(status_code=403, detail="Super admin access required")

        # Return payload with new_token info if refreshed
        payload["new_token"] = new_token
        return payload


@router.post("/workshops")
def admin_create_workshop(
    title: str = Form(None),
    city: str = Form(...),
    location: str = Form(...),
    date: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    style: str = Form(...),
    difficulty: str = Form("intermediate"),
    instructor_name: str = Form(None),
    organizer: str = Form(None),
    description: str = Form(None),
    max_participants: int = Form(0),
    cards: str = Form(None),
    facebook_url: str = Form(None),
    recurrence: str = Form("single"),
    lat: float = Form(None),
    lon: float = Form(None),
    admin: dict = Depends(verify_admin)
):
    """Admin: Create a new workshop. Only admin users can create workshops."""
    admin_id = admin.get("user_id")

    # If lat/lon not provided, try to fetch from predefined_locations
    if lat is None or lon is None:
        with get_db() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT lat, lon FROM predefined_locations WHERE location_name = ? AND city = ?",
                (location, city)
            )
            result = c.fetchone()
            if result:
                lat = result['lat']
                lon = result['lon']
                print(f"✅ Inherited coordinates from predefined_locations: {lat}, {lon}")

    # Apply style-based circular distribution to prevent marker overlap
    if lat is not None and lon is not None:
        lat, lon = apply_style_deviation(lat, lon, style)
        # Apply additional deviation if other workshops of same style exist at this location
        # Get style index for this workshop
        with get_db() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT COUNT(*) FROM workshops WHERE city = ? AND location = ? AND style = ?",
                (city, location, style)
            )
            style_index = c.fetchone()[0]  # Index of this new workshop within its style group

        lat, lon = apply_collision_avoidance_deviation(lat, lon, city, location, style, style_index=style_index)

    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO workshops (admin_id, title, city, location, date, time, start_time, end_time, style, difficulty, instructor_name, organizer, description, max_participants, cards, facebook_url, lat, lon, recurrence) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (admin_id, title, city, location, date, start_time, start_time, end_time, style, difficulty, instructor_name, organizer, description, max_participants, cards, facebook_url, lat, lon, recurrence)
        )
        conn.commit()
        workshop_id = c.lastrowid

    return {"msg": "Workshop created!", "workshop_id": workshop_id}

@router.put("/workshops/{workshop_id}")
def admin_update_workshop(
    workshop_id: int,
    title: str = Form(None),
    city: str = Form(None),
    location: str = Form(None),
    date: str = Form(None),
    start_time: str = Form(None),
    end_time: str = Form(None),
    style: str = Form(None),
    difficulty: str = Form(None),
    instructor_name: str = Form(None),
    organizer: str = Form(None),
    description: str = Form(None),
    cards: str = Form(None),
    facebook_url: str = Form(None),
    recurrence: str = Form(None),
    lat: float = Form(None),
    lon: float = Form(None),
    admin: dict = Depends(verify_admin)
):
    """Admin: Update a workshop they created. Cannot update others' workshops."""
    admin_id = admin.get("user_id")

    # Verify ownership
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT admin_id FROM workshops WHERE id = ?", (workshop_id,))
        result = c.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Workshop not found")

        if result['admin_id'] != admin_id:
            raise HTTPException(status_code=403, detail="You can only edit your own workshops")

    updates = []
    params = []

    if title is not None:
        updates.append("title = ?")
        params.append(title)
    if city:
        updates.append("city = ?")
        params.append(city)
    if location:
        updates.append("location = ?")
        params.append(location)
    if date:
        updates.append("date = ?")
        params.append(date)
    if start_time:
        updates.append("start_time = ?")
        params.append(start_time)
        # Also update the legacy time column for backwards compatibility
        updates.append("time = ?")
        params.append(start_time)
    if end_time:
        updates.append("end_time = ?")
        params.append(end_time)

    # Handle style and coordinate updates
    current_style = style

    # Get current workshop data to use if not being updated
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT style, city, location, date FROM workshops WHERE id = ?", (workshop_id,))
        current_workshop = c.fetchone()
        if not current_workshop:
            raise HTTPException(status_code=404, detail="Workshop not found")

        current_style = current_workshop['style']
        current_city = current_workshop['city']
        current_location = current_workshop['location']
        current_date = current_workshop['date']

    # Use new values if provided, otherwise use current
    updated_style = style if style else current_style
    updated_city = city if city else current_city
    updated_location = location if location else current_location

    if style:
        updates.append("style = ?")
        params.append(style)
        current_style = style

    # Handle coordinates - fetch from predefined_locations if location changed
    if location or (lat is not None or lon is not None):
        # If location changed, fetch new coordinates from predefined_locations
        if location:
            with get_db() as conn:
                c = conn.cursor()
                c.execute(
                    "SELECT lat, lon FROM predefined_locations WHERE location_name = ? AND city = ?",
                    (location, updated_city)
                )
                result = c.fetchone()
                if result:
                    lat = result['lat']
                    lon = result['lon']
                    print(f"Fetched coordinates for {location}: ({lat}, {lon})")

        # Apply circular distribution if coordinates are provided (user explicitly setting them or location change)
        if lat is not None and lon is not None:
            lat, lon = apply_style_deviation(lat, lon, updated_style)
            # Apply collision avoidance for same-style workshops at this location
            # Count other workshops of same style at this location (excluding current)
            with get_db() as conn:
                c = conn.cursor()
                c.execute(
                    "SELECT COUNT(*) FROM workshops WHERE city = ? AND location = ? AND style = ? AND id != ?",
                    (updated_city, updated_location, updated_style, workshop_id)
                )
                style_index = c.fetchone()[0]  # Index among other same-style workshops

            lat, lon = apply_collision_avoidance_deviation(lat, lon, updated_city, updated_location, updated_style, style_index=style_index, exclude_workshop_id=workshop_id)

            updates.append("lat = ?")
            params.append(lat)
            updates.append("lon = ?")
            params.append(lon)

    if difficulty:
        updates.append("difficulty = ?")
        params.append(difficulty)
    if instructor_name:
        updates.append("instructor_name = ?")
        params.append(instructor_name)
    if organizer is not None:
        updates.append("organizer = ?")
        params.append(organizer)
    if description:
        updates.append("description = ?")
        params.append(description)
    if cards is not None:
        updates.append("cards = ?")
        params.append(cards)
    if facebook_url is not None:
        updates.append("facebook_url = ?")
        params.append(facebook_url)
    if recurrence is not None:
        updates.append("recurrence = ?")
        params.append(recurrence)
    if lat is not None:
        updates.append("lat = ?")
        params.append(lat)
    if lon is not None:
        updates.append("lon = ?")
        params.append(lon)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(workshop_id)
    query = f"UPDATE workshops SET {', '.join(updates)} WHERE id = ?"

    with get_db() as conn:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()

    return {"msg": "Workshop updated!"}

@router.delete("/workshops/{workshop_id}")
def admin_delete_workshop(workshop_id: int, admin: dict = Depends(verify_admin)):
    """Admin: Delete a workshop they created. Cannot delete others' workshops."""
    admin_id = admin.get("user_id")

    # Verify ownership
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT admin_id FROM workshops WHERE id = ?", (workshop_id,))
        result = c.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Workshop not found")

        if result['admin_id'] != admin_id:
            raise HTTPException(status_code=403, detail="You can only delete your own workshops")

        c.execute("DELETE FROM workshops WHERE id = ?", (workshop_id,))
        c.execute("DELETE FROM registrations WHERE workshop_id = ?", (workshop_id,))
        conn.commit()

    return {"msg": "Workshop deleted!"}

@router.get("/workshops")
def admin_list_workshops(admin: dict = Depends(verify_admin)):
    """Admin: List only their own workshops with participant counts."""
    admin_id = admin.get("user_id")

    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT w.*, COUNT(r.id) as participant_count
            FROM workshops w
            LEFT JOIN registrations r ON w.id = r.workshop_id
            WHERE w.admin_id = ?
            GROUP BY w.id
            ORDER BY w.date DESC
        """, (admin_id,))
        workshops = c.fetchall()

    return {"workshops": [dict(w) for w in workshops]}

@router.get("/workshops/{workshop_id}/participants")
def admin_get_participants(workshop_id: int, admin: dict = Depends(verify_admin)):
    """Admin: Get detailed participant list for a workshop."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT u.id, u.username, r.registered_at, r.attended
            FROM registrations r
            JOIN users u ON r.user_id = u.id
            WHERE r.workshop_id = ?
            ORDER BY r.registered_at DESC
        """, (workshop_id,))
        participants = c.fetchall()

    return {"participants": [dict(p) for p in participants]}

@router.put("/registrations/{registration_id}/attended")
def admin_mark_attended(
    registration_id: int,
    attended: bool = Form(...),
    admin: dict = Depends(verify_admin)
):
    """Admin: Mark user as attended workshop."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("UPDATE registrations SET attended = ? WHERE id = ?", (int(attended), registration_id))
        conn.commit()

    return {"msg": "Attendance updated!"}

@router.get("/stats")
def admin_get_stats(admin: dict = Depends(verify_admin)):
    """Admin: Get dashboard statistics for their own workshops."""
    admin_id = admin.get("user_id")

    with get_db() as conn:
        c = conn.cursor()

        # Total workshops created by this admin
        c.execute("SELECT COUNT(*) FROM workshops WHERE admin_id = ?", (admin_id,))
        total_workshops = c.fetchone()[0]

        # Total registrations for this admin's workshops
        c.execute("""
            SELECT COUNT(*) FROM registrations 
            WHERE workshop_id IN (SELECT id FROM workshops WHERE admin_id = ?)
        """, (admin_id,))
        total_registrations = c.fetchone()[0]

        # Workshops by style for this admin
        c.execute("""
            SELECT style, COUNT(*) as count
            FROM workshops
            WHERE admin_id = ?
            GROUP BY style
        """, (admin_id,))
        workshops_by_style = {row[0]: row[1] for row in c.fetchall()}

    return {
        "total_workshops": total_workshops,
        "total_registrations": total_registrations,
        "workshops_by_style": workshops_by_style
    }

# Predefined Locations Management
@router.post("/locations")
def admin_create_location(
    country: str = Form(...),
    city: str = Form(...),
    location_name: str = Form(...),
    lat: float = Form(...),
    lon: float = Form(...),
    token: str = Query(...),
    admin: dict = Depends(verify_admin)
):
    """Admin: Create a predefined location with coordinates."""
    admin_id = admin.get("user_id")
    from datetime import datetime

    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO predefined_locations (country, city, location_name, lat, lon, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (country, city, location_name, lat, lon, admin_id, datetime.now().isoformat())
        )
        conn.commit()
        location_id = c.lastrowid

    return {"msg": "Location created!", "location_id": location_id}

@router.get("/locations")
def admin_get_locations(token: str = Query(...), admin: dict = Depends(verify_admin)):
    """Get all predefined locations."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT id, country, city, location_name, lat, lon FROM predefined_locations ORDER BY country, city, location_name")
        locations = [dict(row) for row in c.fetchall()]

    return {"locations": locations}

@router.delete("/locations/{location_id}")
def admin_delete_location(location_id: int, token: str = Query(...), super_admin: dict = Depends(verify_super_admin)):
    """Delete a predefined location (Super Admin only)."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM predefined_locations WHERE id = ?", (location_id,))
        conn.commit()

    return {"msg": "Location deleted!"}

@router.api_route("/locations/{location_id}", methods=["PUT", "POST"])
def admin_update_location(
    location_id: int,
    location_name: str = Form(None),
    country: str = Form(None),
    token: str = Query(...),
    super_admin: dict = Depends(verify_super_admin)
):
    """Update a predefined location (Super Admin only)."""
    updates = []
    params = []

    if location_name is not None:
        updates.append("location_name = ?")
        params.append(location_name)

    if country is not None:
        updates.append("country = ?")
        params.append(country)

    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    params.append(location_id)

    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            f"UPDATE predefined_locations SET {', '.join(updates)} WHERE id = ?",
            params
        )
        conn.commit()

    return {"msg": "Location updated!"}

# User Management (Super Admin Only)
@router.get("/users")
def super_admin_get_users(super_admin: dict = Depends(verify_super_admin)):
    """Super Admin: Get all users with their admin status."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT id, username, is_admin, is_super_admin FROM users ORDER BY username")
        users = [dict(row) for row in c.fetchall()]

    return {"users": users}

@router.put("/users/{user_id}/admin-status")
def super_admin_toggle_user_admin(
    user_id: int,
    is_admin: bool = Form(...),
    super_admin: dict = Depends(verify_super_admin)
):
    """Super Admin: Toggle admin status for a user."""
    with get_db() as conn:
        c = conn.cursor()

        # Prevent modifying super_admin users (except super_admin themselves)
        c.execute("SELECT is_super_admin FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user['is_super_admin'] and user_id != super_admin.get("user_id"):
            raise HTTPException(status_code=403, detail="Cannot modify super_admin status of other super_admins")

        # Update admin status
        c.execute("UPDATE users SET is_admin = ? WHERE id = ?", (int(is_admin), user_id))
        conn.commit()

    status = "admin" if is_admin else "non-admin"
    return {"msg": f"User updated to {status}", "user_id": user_id, "is_admin": is_admin}

