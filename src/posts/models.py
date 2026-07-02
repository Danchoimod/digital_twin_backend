from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base
from src.models import TimestampMixin


class Post(Base, TimestampMixin):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    image_url = Column(String, nullable=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    creator = relationship("User")
