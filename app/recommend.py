from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from .database import get_db
from datetime import datetime
from pathlib import Path
import shutil
import os

router = APIRouter()

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("frontend/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/recommend/song/photo")
def recommend_song_photo(user_id: int = Form(...), file: UploadFile = File(...)):
    """Upload a photo and save it to disk."""
    try:
        # Generate unique filename
        filename = f"{user_id}_{datetime.now().timestamp()}_{file.filename}"
        filepath = UPLOAD_DIR / filename

        # Save file to disk
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Store in database with relative path for serving
        relative_path = f"/uploads/{filename}"

        with get_db() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO songs (user_id, name, image_path, created_at) VALUES (?, ?, ?, ?)",
                (user_id, file.filename, relative_path, datetime.now().isoformat())
            )
            conn.commit()

        return {"msg": f"Photo '{file.filename}' uploaded successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload photo: {str(e)}")

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

@router.post("/recommend/song/url")
def recommend_song_url(user_id: int = Form(...), song_url: str = Form(...)):
    """Add a song from YouTube or Spotify URL."""
    # Validate URL
    if not song_url:
        raise HTTPException(status_code=400, detail="URL is required")

    # Extract platform and validate
    if 'youtube.com' in song_url or 'youtu.be' in song_url:
        platform = "YouTube"
    elif 'spotify.com' in song_url:
        platform = "Spotify"
    else:
        raise HTTPException(status_code=400, detail="Only YouTube and Spotify URLs are supported")

    # Extract song name from URL or use platform as fallback
    try:
        if platform == "Spotify":
            # Extract track name from Spotify URL
            parts = song_url.split('/')
            song_name = parts[-1].split('?')[0].replace('-', ' ').title()
        else:
            # YouTube - use URL as identifier
            song_name = f"{platform} Link"
    except:
        song_name = f"{platform} Link"

    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO songs (user_id, name, image_path, created_at) VALUES (?, ?, ?, ?)",
            (user_id, song_name, song_url, datetime.now().isoformat())
        )
        conn.commit()

    return {"msg": f"✅ {platform} link added successfully!"}

@router.get("/songs/{user_id}")
def get_user_songs(user_id: int):
    """Get all songs for a user."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT id, name, image_path, created_at FROM songs WHERE user_id = ?", (user_id,))
        songs = c.fetchall()
    return {"songs": [dict(s) for s in songs]}

