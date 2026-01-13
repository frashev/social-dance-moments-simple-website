from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from .database import get_db
from datetime import datetime

router = APIRouter()

@router.post("/recommend/song/photo")
def recommend_song_photo(user_id: int = Form(...), file: UploadFile = File(...)):
    """Upload a photo and optionally add song info."""
    # TODO: Add OCR/image analysis to extract song info
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO songs (user_id, name, image_path, created_at) VALUES (?, ?, ?, ?)",
            (user_id, f"Photo from {file.filename}", file.filename, datetime.now().isoformat())
        )
        conn.commit()
    return {"msg": "Photo received and stored."}

@router.post("/recommend/song/manual")
def recommend_song_manual(user_id: int = Form(...), song_name: str = Form(...)):
    """Manually add a song recommendation."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO songs (user_id, name, created_at) VALUES (?, ?, ?)",
            (user_id, song_name, datetime.now().isoformat())
        )
        conn.commit()
    return {"msg": f"Song '{song_name}' saved!"}

@router.get("/songs/{user_id}")
def get_user_songs(user_id: int):
    """Get all songs for a user."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT id, name, created_at FROM songs WHERE user_id = ?", (user_id,))
        songs = c.fetchall()
    return {"songs": [dict(s) for s in songs]}

