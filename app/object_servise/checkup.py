import datetime
from typing import Optional, Tuple

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class TimeRequest(BaseModel):
    date: datetime.date
    hour_range: Tuple[int, int]


class CheckupResponse(BaseModel):
    login: str
    checkup_time: datetime.datetime
    place: int


class Checkup(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    login: str
    checkup_time: Optional[datetime.datetime] = None
    place: int
    status: str
    # time: datetime.datetime = Field(default_factory=datetime.datetime.now)
