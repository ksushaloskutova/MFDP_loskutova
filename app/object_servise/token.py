from sqlmodel import SQLModel, Field
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel
import jwt
import os
from dotenv import load_dotenv

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()  # Загружаем переменные окружения из .env

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 90


class TokenResponse(BaseModel):
    chat_id: str


class Token(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    chat_id: str
    token: str
    def __init__(self, chat_id, login) -> None:
        self.chat_id = chat_id
        self.token = self.encode_token(login)

    def encode_token(self, login):
        to_encode = {"login": login}
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        # Храним expire как UNIX-время
        to_encode.update({"expire": int(expire.timestamp())})

        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return token

    def verify_token(self):
        try:
            payload = jwt.decode(self.token, SECRET_KEY, algorithms=[ALGORITHM])
            logger.info(f"LOGIN = {payload }")
            login = payload.get("login")  # Получаем идентификатор пользователя
            expire = payload.get("expire")
            if expire is None or datetime.utcnow() > datetime.fromtimestamp(expire):
                return None
            return login
        except jwt.PyJWTError:
            return None