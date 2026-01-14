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
    city: str
    location: str
    date: str  # ISO format
    time: str  # HH:MM
    style: str  # salsa, bachata, etc.

