from fastapi import APIRouter, Form, HTTPException, Query
from .database import get_db
from .geocoding import get_city_coordinates, get_workshop_coordinates, calculate_distance, WORKSHOP_GEOCODING_CACHE
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/workshops")
def get_workshops(
    style: str = Query(None),
    city: str = Query(None),
    difficulty: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None)
):
    """Get all workshops with optional filtering."""
    with get_db() as conn:
        c = conn.cursor()

        # Build query with filters
        query = "SELECT id, title, city, location, date, start_time, end_time, style, difficulty, instructor_name, description, cards, lat, lon, facebook_url, recurrence FROM workshops WHERE 1=1"
        params = []

        if style:
            query += " AND style = ?"
            params.append(style)
        if city:
            query += " AND city LIKE ?"
            params.append(f"%{city}%")
        if difficulty:
            query += " AND difficulty = ?"
            params.append(difficulty)
        if date_from:
            query += " AND date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND date <= ?"
            params.append(date_to)

        c.execute(query, params)
        workshops = c.fetchall()

    # Add participant count
    result = []
    for w in workshops:
        w_dict = dict(w)

        # Count participants
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM registrations WHERE workshop_id = ?", (w['id'],))
            w_dict['participant_count'] = c.fetchone()[0]

        result.append(w_dict)

    return {"workshops": result}

@router.get("/workshops/nearby")
def get_nearby_workshops(
    lat: float = Query(...),
    lon: float = Query(...),
    radius_km: float = Query(10)
):
    """Get workshops within a radius of user location."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT id, title, city, location, date, start_time, end_time, style, difficulty FROM workshops")
        workshops = c.fetchall()

    nearby = []
    for w in workshops:
        coords = get_city_coordinates(w['city'])
        if coords:
            distance = calculate_distance(lat, lon, coords[0], coords[1])
            if distance <= radius_km:
                w_dict = dict(w)
                w_dict['lat'] = coords[0]
                w_dict['lon'] = coords[1]
                w_dict['distance_km'] = round(distance, 2)
                nearby.append(w_dict)

    # Sort by distance
    nearby.sort(key=lambda x: x['distance_km'])
    return {"nearby_workshops": nearby}

@router.post("/workshops")
def create_workshop(
    title: str = Form(None),
    city: str = Form(...),
    location: str = Form(...),
    date: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    style: str = Form(...),
    difficulty: str = Form("intermediate"),
    instructor_name: str = Form(None),
    description: str = Form(None),
    cards: str = Form(None)
):
    """Create a new workshop and geocode coordinates."""
    # Geocode the workshop location
    coords = get_workshop_coordinates(location, city)
    lat, lon = None, None

    if coords:
        lat, lon = coords
        logger.info(f"✅ Geocoded {location}, {city} -> ({lat}, {lon})")
    else:
        logger.warning(f"⚠️  Failed to geocode {location}, {city}")

    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO workshops (title, city, location, date, time, start_time, end_time, style, difficulty, instructor_name, description, cards, lat, lon) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (title, city, location, date, start_time, start_time, end_time, style, difficulty, instructor_name, description, cards, lat, lon)
        )
        conn.commit()
    return {"msg": "Workshop created!", "lat": lat, "lon": lon}

@router.post("/workshops/{workshop_id}/register")
def register_for_workshop(workshop_id: int, user_id: int = Query(...)):
    """Register user for a workshop."""
    with get_db() as conn:
        c = conn.cursor()

        # Check if already registered
        c.execute("SELECT id FROM registrations WHERE user_id = ? AND workshop_id = ?", (user_id, workshop_id))
        if c.fetchone():
            raise HTTPException(status_code=409, detail="You're already registered for this workshop!")

        # Check if workshop exists
        c.execute("SELECT id FROM workshops WHERE id = ?", (workshop_id,))
        if not c.fetchone():
            raise HTTPException(status_code=404, detail="Workshop not found.")

        try:
            c.execute(
                "INSERT INTO registrations (user_id, workshop_id, registered_at) VALUES (?, ?, ?)",
                (user_id, workshop_id, datetime.now().isoformat())
            )
            conn.commit()
            return {"msg": "✅ Successfully registered for the workshop!"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Registration error: {str(e)}")

@router.delete("/workshops/{workshop_id}/register")
def cancel_registration(workshop_id: int, user_id: int = Query(...)):
    """Cancel workshop registration."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM registrations WHERE user_id = ? AND workshop_id = ?", (user_id, workshop_id))
        conn.commit()
    return {"msg": "Registration cancelled"}

@router.get("/workshops/{workshop_id}/participants")
def get_participants(workshop_id: int):
    """Get registered participants for a workshop (admin-only)."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT u.id, u.username 
            FROM registrations r 
            JOIN users u ON r.user_id = u.id 
            WHERE r.workshop_id = ?
        """, (workshop_id,))
        participants = c.fetchall()

    return {"participants": [dict(p) for p in participants]}

