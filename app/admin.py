from fastapi import APIRouter, Form, HTTPException, Depends, Query
from .database import get_db
from .utils import verify_token
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["admin"])

def verify_admin(token: str = Query(...)) -> dict:
    """Verify that user is admin."""
    payload = verify_token(token)
    if not payload or not payload.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return payload

@router.post("/workshops")
def admin_create_workshop(
    city: str = Form(...),
    location: str = Form(...),
    date: str = Form(...),
    time: str = Form(...),
    style: str = Form(...),
    difficulty: str = Form("intermediate"),
    instructor_name: str = Form(None),
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

    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO workshops (admin_id, city, location, date, time, style, difficulty, instructor_name, description, max_participants, cards, facebook_url, lat, lon, recurrence) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (admin_id, city, location, date, time, style, difficulty, instructor_name, description, max_participants, cards, facebook_url, lat, lon, recurrence)
        )
        conn.commit()
        workshop_id = c.lastrowid

    return {"msg": "Workshop created!", "workshop_id": workshop_id}

@router.put("/workshops/{workshop_id}")
def admin_update_workshop(
    workshop_id: int,
    city: str = Form(None),
    location: str = Form(None),
    date: str = Form(None),
    time: str = Form(None),
    style: str = Form(None),
    difficulty: str = Form(None),
    instructor_name: str = Form(None),
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

    if city:
        updates.append("city = ?")
        params.append(city)
    if location:
        updates.append("location = ?")
        params.append(location)
    if date:
        updates.append("date = ?")
        params.append(date)
    if time:
        updates.append("time = ?")
        params.append(time)
    if style:
        updates.append("style = ?")
        params.append(style)
    if difficulty:
        updates.append("difficulty = ?")
        params.append(difficulty)
    if instructor_name:
        updates.append("instructor_name = ?")
        params.append(instructor_name)
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
            "INSERT INTO predefined_locations (city, location_name, lat, lon, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (city, location_name, lat, lon, admin_id, datetime.now().isoformat())
        )
        conn.commit()
        location_id = c.lastrowid

    return {"msg": "Location created!", "location_id": location_id}

@router.get("/locations")
def admin_get_locations(token: str = Query(...), admin: dict = Depends(verify_admin)):
    """Get all predefined locations."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT id, city, location_name, lat, lon FROM predefined_locations ORDER BY city, location_name")
        locations = [dict(row) for row in c.fetchall()]

    return {"locations": locations}

@router.delete("/locations/{location_id}")
def admin_delete_location(location_id: int, token: str = Query(...), admin: dict = Depends(verify_admin)):
    """Delete a predefined location."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM predefined_locations WHERE id = ?", (location_id,))
        conn.commit()

    return {"msg": "Location deleted!"}
