from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import jwt

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# JWT Secret - In production, use environment variable
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10080  # 7 days (was 30 minutes)

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

def verify_token_with_refresh(token: str) -> tuple[Optional[dict], Optional[str]]:
    """
    Verify token and return (payload, new_token).
    If token is expired, attempts to refresh it.
    Returns (payload, None) if still valid.
    Returns (payload, new_token) if refreshed.
    Returns (None, None) if invalid.
    """
    try:
        # Try to decode without verification to check expiration
        unverified = jwt.decode(token, options={"verify_signature": False})
        user_id = unverified.get("user_id")
        is_admin = unverified.get("is_admin", False)

        # Try normal verification
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return (payload, None)  # Token still valid

    except jwt.ExpiredSignatureError:
        # Token expired - refresh it
        try:
            unverified = jwt.decode(token, options={"verify_signature": False})
            user_id = unverified.get("user_id")
            is_admin = unverified.get("is_admin", False)

            if user_id:
                new_token = create_access_token(user_id, is_admin)
                # Return the unverified payload (it's still valid data) and new token
                return (unverified, new_token)
        except Exception:
            pass

        return (None, None)  # Can't refresh

    except jwt.InvalidTokenError:
        return (None, None)  # Invalid token

def should_refresh_token(token: str) -> bool:
    """
    Check if token should be refreshed (within 10% of expiration).
    Helps refresh proactively before actual expiration.
    """
    try:
        unverified = jwt.decode(token, options={"verify_signature": False})
        exp = unverified.get("exp")
        iat = unverified.get("iat")

        if not exp or not iat:
            return False

        token_lifetime = exp - iat
        current_time = datetime.utcnow().timestamp()
        time_left = exp - current_time
        threshold = token_lifetime * 0.1  # 10% of token lifetime

        return time_left < threshold
    except Exception:
        return False

