from pydantic import BaseModel
from typing import Optional
from pathlib import Path

class User(BaseModel):
    id: int
    username: str
    password_hash: str
    is_super_admin: bool = False

class Song(BaseModel):
    id: int
    user_id: int
    name: str
    image_path: Optional[Path]

class Workshop(BaseModel):
    id: int
    admin_id: Optional[int]
    title: Optional[str] = None
    city: str
    location: str
    date: str  # ISO format
    time: str  # HH:MM
    style: str  # salsa, bachata, etc.

class Event(BaseModel):
    id: int
    admin_id: int
    title: str
    photo_path: Optional[str]
    event_organizer: str
    location: str
    city: str
    start_date: str  # ISO format
    start_time: str  # HH:MM
    end_date: str  # ISO format
    end_time: str  # HH:MM
    description: Optional[str]
    facebook_url: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    created_at: Optional[str]

