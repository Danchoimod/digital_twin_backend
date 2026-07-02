from sqlalchemy.orm import Session
from src.auth.models import User
from src.auth.schemas import UserCreate
from src.auth.utils import hash_password


class AuthService:
    @staticmethod
    def get_user_by_email(db: Session, email: str):
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create_user(db: Session, user_in: UserCreate):
        hashed = hash_password(user_in.password)
        db_user = User(email=user_in.email, hashed_password=hashed)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
