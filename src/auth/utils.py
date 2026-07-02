import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Any


def hash_password(password: str) -> str:
    """Simple password hashing using hashlib (prefer passlib/bcrypt in production)"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password


def create_access_token(data: Dict[str, Any], expires_delta: timedelta = timedelta(minutes=30)) -> str:
    """Mock JWT token generation. In real app, use PyJWT / jose"""
    payload = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    payload.update({"exp": expire.isoformat()})
    # Simple encoded mock token
    import base64
    import json
    payload_str = json.dumps(payload)
    return base64.urlsafe_b64encode(payload_str.encode()).decode().rstrip("=")
