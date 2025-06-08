from sqlmodel import SQLModel, Field
from typing import Optional
import datetime
from fastapi import Request
from typing import Optional, List
from pydantic import BaseModel
from typing import List, Dict, Tuple


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


