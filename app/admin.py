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
    admin: dict = Depends(verify_admin)
):
    """Admin: Create a new workshop."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO workshops (city, location, date, time, style, difficulty, instructor_name, description, max_participants) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (city, location, date, time, style, difficulty, instructor_name, description, max_participants)
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
    admin: dict = Depends(verify_admin)
):
    """Admin: Update a workshop."""
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
    """Admin: Delete a workshop."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM workshops WHERE id = ?", (workshop_id,))
        c.execute("DELETE FROM registrations WHERE workshop_id = ?", (workshop_id,))
        conn.commit()

    return {"msg": "Workshop deleted!"}

@router.get("/workshops")
def admin_list_workshops(admin: dict = Depends(verify_admin)):
    """Admin: List all workshops with participant counts."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT w.*, COUNT(r.id) as participant_count
            FROM workshops w
            LEFT JOIN registrations r ON w.id = r.workshop_id
            GROUP BY w.id
            ORDER BY w.date DESC
        """)
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
    """Admin: Get dashboard statistics."""
    with get_db() as conn:
        c = conn.cursor()

        # Total workshops
        c.execute("SELECT COUNT(*) FROM workshops")
        total_workshops = c.fetchone()[0]

        # Total registrations
        c.execute("SELECT COUNT(*) FROM registrations")
        total_registrations = c.fetchone()[0]

        # Total users
        c.execute("SELECT COUNT(*) FROM users")
        total_users = c.fetchone()[0]

        # Workshops by style
        c.execute("""
            SELECT style, COUNT(*) as count
            FROM workshops
            GROUP BY style
        """)
        workshops_by_style = {row[0]: row[1] for row in c.fetchall()}

    return {
        "total_workshops": total_workshops,
        "total_registrations": total_registrations,
        "total_users": total_users,
        "workshops_by_style": workshops_by_style
    }

