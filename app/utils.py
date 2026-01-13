from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import jwt

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# JWT Secret - In production, use environment variable
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def hash_password(password: str) -> str:
    """Hash a plain password using Argon2."""
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against hash."""
    return pwd_context.verify(plain, hashed)

def create_access_token(user_id: int, is_admin: bool = False) -> str:
    """Create a JWT access token."""
    payload = {
        "user_id": user_id,
        "is_admin": is_admin,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token. Returns payload or None if invalid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

