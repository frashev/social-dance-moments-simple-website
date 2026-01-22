from fastapi import APIRouter, Form, HTTPException, Query, UploadFile, File, Request
from .database import get_db
from .geocoding import get_workshop_coordinates
from datetime import datetime
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = Path(__file__).parent.parent / "frontend" / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


def fetch_predefined_location(location: str, city: str):
    if not location or not city:
        return None

    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT country, lat, lon FROM predefined_locations WHERE location_name = ? AND city = ?",
            (location, city)
        )
        result = c.fetchone()

    if result:
        return result["country"], result["lat"], result["lon"]

    return None

@router.get("/events")
def get_events(admin_id: int | None = Query(default=None)):
    """Get events, optionally filtered by admin_id."""
    with get_db() as conn:
        c = conn.cursor()
        if admin_id is None:
            c.execute("""
                SELECT id, title, photo_path, event_organizer, location, country, city, 
                       start_date, start_time, end_date, end_time, description, 
                       facebook_url, lat, lon, created_at 
                FROM events 
                ORDER BY start_date ASC, start_time ASC
            """)
        else:
            c.execute("""
                SELECT id, title, photo_path, event_organizer, location, country, city, 
                       start_date, start_time, end_date, end_time, description, 
                       facebook_url, lat, lon, created_at 
                FROM events 
                WHERE admin_id = ?
                ORDER BY start_date ASC, start_time ASC
            """, (admin_id,))
        events = c.fetchall()

    return {"events": [dict(e) for e in events]}


@router.get("/locations")
def get_locations():
    """Get predefined locations for public filters."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT id,
                   COALESCE(country, 'Unknown') AS country,
                   city,
                   location_name,
                   lat,
                   lon
            FROM predefined_locations
            ORDER BY country, city, location_name
        """)
        locations = [dict(row) for row in c.fetchall()]

    return {"locations": locations}

@router.post("/events")
async def create_event(
    request: Request,
    admin_id: int = Query(...)
):
    """Create a new event with optional photo and geocode coordinates."""

    form_data = await request.form()

    # Extract all form fields
    title = form_data.get('title', '').strip()
    event_organizer = form_data.get('event_organizer', '').strip()
    location = form_data.get('location', '').strip()
    city = form_data.get('city', '').strip()
    start_date = form_data.get('start_date', '')
    start_time = form_data.get('start_time', '')
    end_date = form_data.get('end_date', '')
    end_time = form_data.get('end_time', '')
    description = form_data.get('description', '').strip()
    facebook_url = form_data.get('facebook_url', '').strip()
    lat = form_data.get('lat')
    lon = form_data.get('lon')
    photo = form_data.get('photo')
    photo_path_input = form_data.get('photo_path')

    # Convert lat/lon to float if they exist
    try:
        lat = float(lat) if lat else None
        lon = float(lon) if lon else None
    except (ValueError, TypeError):
        lat = None
        lon = None

    # Handle photo upload or use existing photo path from duplicate
    final_photo_path = None

    if photo:
        if hasattr(photo, 'filename') and photo.filename:
            try:
                timestamp = datetime.now().timestamp()
                file_ext = os.path.splitext(photo.filename)[1]
                unique_filename = f"event_{timestamp}{file_ext}"
                final_photo_path = f"uploads/{unique_filename}"

                file_location = UPLOAD_DIR / unique_filename
                with open(file_location, "wb+") as file_object:
                    file_object.write(photo.file.read())

                logger.info(f"✅ Uploaded photo: {final_photo_path}")
            except Exception as e:
                logger.error(f"❌ Failed to upload photo: {str(e)}", exc_info=True)
    elif photo_path_input:
        # Use photo path from duplicate
        final_photo_path = str(photo_path_input).strip()
        logger.info(f"✅ Using duplicate photo: {final_photo_path}")

    # Use passed coordinates if available, otherwise fall back to predefined locations, then geocode
    final_country = None
    final_lat, final_lon = None, None

    if lat is not None and lon is not None:
        final_lat, final_lon = lat, lon
    else:
        result = fetch_predefined_location(location, city)
        if result:
            final_country, final_lat, final_lon = result
        else:
            # Geocode the event location
            coords = get_workshop_coordinates(location, city)
            if coords:
                final_lat, final_lon = coords
    if final_country is None:
        result = fetch_predefined_location(location, city)
        if result:
            final_country, _, _ = result

    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            """INSERT INTO events 
            (admin_id, title, photo_path, event_organizer, location, country, city, 
             start_date, start_time, end_date, end_time, description, 
             facebook_url, lat, lon, created_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (admin_id, title, final_photo_path, event_organizer, location, final_country, city,
             start_date, start_time, end_date, end_time, description,
             facebook_url, final_lat, final_lon, datetime.now().isoformat())
        )
        conn.commit()
        event_id = c.lastrowid

    return {
        "msg": "Event created successfully!",
        "event_id": event_id,
        "photo_path": final_photo_path,
        "lat": final_lat,
        "lon": final_lon
    }

@router.get("/events/{event_id}")
def get_event(event_id: int):
    """Get specific event details."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT id, title, photo_path, event_organizer, location, country, city, 
                   start_date, start_time, end_date, end_time, description, 
                   facebook_url, lat, lon, created_at 
            FROM events 
            WHERE id = ?
        """, (event_id,))
        event = c.fetchone()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return {"event": dict(event)}

@router.put("/events/{event_id}")
def update_event(
    event_id: int,
    title: str = Form(...),
    event_organizer: str = Form(...),
    location: str = Form(...),
    city: str = Form(...),
    start_date: str = Form(...),
    start_time: str = Form(...),
    end_date: str = Form(...),
    end_time: str = Form(...),
    description: str = Form(None),
    facebook_url: str = Form(None),
    lat: float = Form(None),
    lon: float = Form(None),
    photo: UploadFile = File(None)
):
    """Update event details."""

    with get_db() as conn:
        c = conn.cursor()

        # Get current event
        c.execute("SELECT photo_path FROM events WHERE id = ?", (event_id,))
        result = c.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Event not found")

        photo_path = result[0]

        # Handle photo upload
        if photo and photo.filename:
            try:
                timestamp = datetime.now().timestamp()
                file_ext = os.path.splitext(photo.filename)[1]
                unique_filename = f"event_{timestamp}{file_ext}"
                photo_path = f"uploads/{unique_filename}"

                file_location = UPLOAD_DIR / unique_filename
                with open(file_location, "wb+") as file_object:
                    file_object.write(photo.file.read())

                logger.info(f"✅ Updated event photo: {photo_path}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to upload photo: {str(e)}")

        # Use passed coordinates if available, otherwise fall back to predefined locations, then geocode
        final_country = None
        final_lat, final_lon = None, None
        if lat is not None and lon is not None:
            final_lat, final_lon = lat, lon
        else:
            result = fetch_predefined_location(location, city)
            if result:
                final_country, final_lat, final_lon = result
            else:
                coords = get_workshop_coordinates(location, city)
                if coords:
                    final_lat, final_lon = coords
        if final_country is None:
            result = fetch_predefined_location(location, city)
            if result:
                final_country, _, _ = result

        c.execute(
            """UPDATE events 
            SET title = ?, event_organizer = ?, location = ?, city = ?, 
                country = ?, start_date = ?, start_time = ?, end_date = ?, end_time = ?, 
                description = ?, facebook_url = ?, photo_path = ?, lat = ?, lon = ? 
            WHERE id = ?""",
            (title, event_organizer, location, city, final_country, start_date, start_time,
             end_date, end_time, description, facebook_url, photo_path, final_lat, final_lon, event_id)
        )
        conn.commit()

    return {"msg": "Event updated successfully!"}

@router.delete("/events/{event_id}")
def delete_event(event_id: int):
    """Delete an event."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM events WHERE id = ?", (event_id,))
        conn.commit()

    return {"msg": "Event deleted successfully!"}

