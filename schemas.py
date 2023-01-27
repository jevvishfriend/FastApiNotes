from datetime import datetime
from pydantic import BaseModel


class NotePydantic(BaseModel):
    id: int
    data: str
    date: datetime

    class Config:
        orm_mode = True
