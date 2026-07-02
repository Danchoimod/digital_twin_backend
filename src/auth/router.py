from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.database import get_db
from src.auth.schemas import UserCreate, UserResponse, Token
from src.auth.service import AuthService
from src.auth.utils import verify_password, create_access_token
from src.auth.exceptions import InvalidCredentialsException
from src.exceptions import CustomBaseException

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    db_user = AuthService.get_user_by_email(db, email=user_in.email)
    if db_user:
        raise CustomBaseException(detail="Email already registered")
    return AuthService.create_user(db, user_in)


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = AuthService.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise InvalidCredentialsException()
    
    access_token = create_access_token(data={"email": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
