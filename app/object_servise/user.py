import hashlib
import os
import re
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class UserResponse(BaseModel):
    login: str
    password: str
    chat_id: Optional[str] = ""

    def check_password(self):
        if len(self.password) < 6:
            return False

        if not re.search(r'\d', self.password):
            return False

        if not re.search(r'[a-zA-Z]', self.password):
            return False
        return True

    def check_email(self):
        if not self.login:
            return False

        if not re.match(r"[^@]+@[^@]+\.[^@]+", self.login):
            return False
        return True


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    login: Optional[str] = None
    hash_password: str = Field(default=None)
    role: str

    def __init__(self, user: UserResponse, role: str = "user") -> None:
        self.login = user.login
        self.hash_password = self.__password_hashing(user.password)
        self.role = role

    def __password_hashing(self, password: str) -> str:
        salt = os.urandom(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return salt.hex() + pwd_hash.hex()

    def verify_password(self, provided_password: str) -> bool:
        salt = bytes.fromhex(self.hash_password[:32])
        stored_hash = self.hash_password[32:]
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256', provided_password.encode(), salt, 100000
        )
        return pwd_hash.hex() == stored_hash
