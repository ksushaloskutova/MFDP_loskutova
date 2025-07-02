from typing import List, Optional

from database.config import get_settings
from object_servise.user import User, UserResponse


def get_all_users(session) -> Optional[List[User]]:
    return session.query(User).all()


def get_user_by_login(login: str, session) -> Optional[User]:
    return session.query(User).filter(User.login == login).first()


def create_user(new_user: UserResponse, session) -> None:
    if new_user.check_password() and new_user.check_email():
        new_user_db = User(new_user)
        session.add(new_user_db)
        session.commit()
        session.refresh(new_user_db)
        return True
    else:
        return False


def autorization_user(User_in_db: User, provided_password: str) -> bool:
    return User_in_db.verify_password(provided_password)


def create_admin(session) -> None:
    admin = User(
        user=UserResponse(
            login=get_settings().ADMIN_LOGIN, password=get_settings().ADMIN_PASSWORD
        ),
        role="admin",
    )
    # Проверка, существует ли администратор в базе данных
    with session:
        if not get_user_by_login(admin.login, session):
            session.add(admin)
            session.commit()


def create_test_user(session) -> None:
    test_user = User(
        user=UserResponse(login="testov@mail.ru", password="12345a"), role="user"
    )
    with session:
        if not get_user_by_login(test_user.login, session):
            session.add(test_user)
            session.commit()
