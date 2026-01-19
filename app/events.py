from fastapi import APIRouter, Form, HTTPException, Query, UploadFile, File
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

@router.get("/events")
def get_events():
    """Get all events."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT id, title, photo_path, event_organizer, location, city, 
                   start_date, start_time, end_date, end_time, description, 
                   facebook_url, lat, lon, created_at 
            FROM events 
            ORDER BY start_date ASC, start_time ASC
        """)
        events = c.fetchall()

    return {"events": [dict(e) for e in events]}

@router.post("/events")
def create_event(
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
    photo: UploadFile = File(None),
    admin_id: int = Query(...),
    lat: float = Form(None),
    lon: float = Form(None)
):
    """Create a new event with optional photo and geocode coordinates."""

    # Handle photo upload
    photo_path = None
    if photo and photo.filename:
        try:
            # Create unique filename
            timestamp = datetime.now().timestamp()
            file_ext = os.path.splitext(photo.filename)[1]
            unique_filename = f"event_{timestamp}{file_ext}"
            photo_path = f"uploads/{unique_filename}"

            file_location = UPLOAD_DIR / unique_filename
            with open(file_location, "wb+") as file_object:
                file_object.write(photo.file.read())

            logger.info(f"✅ Uploaded event photo: {photo_path}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to upload photo: {str(e)}")

    # Use passed coordinates if available from predefined locations, otherwise geocode
    final_lat, final_lon = None, None

    if lat is not None and lon is not None:
        final_lat, final_lon = lat, lon
        logger.info(f"✅ Using predefined location coordinates: ({final_lat}, {final_lon})")
    else:
        # Geocode the event location
        coords = get_workshop_coordinates(location, city)
        if coords:
            final_lat, final_lon = coords
            logger.info(f"✅ Geocoded {location}, {city} -> ({final_lat}, {final_lon})")
        else:
            logger.warning(f"⚠️ Failed to geocode {location}, {city}")

    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            """INSERT INTO events 
            (admin_id, title, photo_path, event_organizer, location, city, 
             start_date, start_time, end_date, end_time, description, 
             facebook_url, lat, lon, created_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (admin_id, title, photo_path, event_organizer, location, city,
             start_date, start_time, end_date, end_time, description,
             facebook_url, final_lat, final_lon, datetime.now().isoformat())
        )
        conn.commit()
        event_id = c.lastrowid

    return {
        "msg": "Event created successfully!",
        "event_id": event_id,
        "lat": final_lat,
        "lon": final_lon
    }

@router.get("/events/{event_id}")
def get_event(event_id: int):
    """Get specific event details."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT id, title, photo_path, event_organizer, location, city, 
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

        # Geocode the event location
        coords = get_workshop_coordinates(location, city)
        lat, lon = None, None

        if coords:
            lat, lon = coords

        c.execute(
            """UPDATE events 
            SET title = ?, event_organizer = ?, location = ?, city = ?, 
                start_date = ?, start_time = ?, end_date = ?, end_time = ?, 
                description = ?, facebook_url = ?, photo_path = ?, lat = ?, lon = ? 
            WHERE id = ?""",
            (title, event_organizer, location, city, start_date, start_time,
             end_date, end_time, description, facebook_url, photo_path, lat, lon, event_id)
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

