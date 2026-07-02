# Import declarative base for reuse in other modules
from src.database import Base

# Place any shared database models or mixins here (e.g., TimestampMixin)
from sqlalchemy import Column, DateTime, func


class TimestampMixin:
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
