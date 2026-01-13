from fastapi import APIRouter, Form, HTTPException
from .database import get_db
from .utils import hash_password, verify_password, create_access_token

router = APIRouter()

@router.post("/register")
def register(username: str = Form(...), password: str = Form(...)):
    """Register a new user."""
    with get_db() as conn:
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                      (username, hash_password(password)))
            conn.commit()
            user_id = c.lastrowid
            token = create_access_token(user_id, is_admin=False)
            return {"msg": "User registered successfully", "access_token": token, "user_id": user_id}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")

@router.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    """Login user and return JWT access token."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT id, password_hash, is_admin FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        if not user or not verify_password(password, user[1]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user_id = user[0]
        is_admin = bool(user[2])
        token = create_access_token(user_id, is_admin=is_admin)
        return {"msg": "Login successful", "access_token": token, "user_id": user_id, "username": username, "is_admin": is_admin}

