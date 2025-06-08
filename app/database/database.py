
from sqlmodel import SQLModel, Session, create_engine
from .config import get_settings
from fastapi import Depends
from interaction_servise import user_interaction as UserServise
from interaction_servise import  checkup_interaction as CheckupServise
from object_servise.User import User, UserResponse
from object_servise.Token import Token
from object_servise.Checkup import Checkup

engine = create_engine(url=get_settings().DATABASE_URL_psycopg,
                       echo=True, pool_size=5, max_overflow=10)

session = Session(engine)

def get_session():
    with Session(engine) as session:
        yield session



def init_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        UserServise.create_admin(session)
        UserServise.create_test_user(session)
        CheckupServise.create_checkup_test(session)
