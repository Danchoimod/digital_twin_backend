import base64
import json
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.database import get_db
from src.auth.exceptions import InvalidCredentialsException
from src.auth.service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Dependency to get the current authenticated user.
    """
    try:
        # Decode the mock token
        padding = "=" * (4 - len(token) % 4)
        decoded_bytes = base64.urlsafe_b64decode(token + padding)
        payload = json.loads(decoded_bytes.decode())
        email: str = payload.get("email")
        if email is None:
            raise InvalidCredentialsException()
    except Exception:
        raise InvalidCredentialsException()

    user = AuthService.get_user_by_email(db, email=email)
    if user is None:
        raise InvalidCredentialsException()
    return user
