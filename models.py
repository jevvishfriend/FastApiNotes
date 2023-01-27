from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from database import Base, get_db


class NoteOut(BaseModel):
    id: int
    data: str
    date: datetime


class NotePydantic(BaseModel):
    id: int
    data: str
    date: datetime

    class Config:
        orm_mode = True


class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    data = Column(String(10000))
    date = Column(DateTime(timezone=True), default=func.now())

