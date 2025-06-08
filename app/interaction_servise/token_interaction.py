from datetime import datetime, timedelta, timezone
from typing import List, Optional
from object_servise.Token import Token
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_token_by_chat_id(chat_id: str, session) -> Optional[Token]:
    return session.query(Token).filter(Token.chat_id == chat_id).first()

def create_access_token(data: dict, session):
    login = data["login"]
    chat_id = data["chat_id"]
    token_table = Token(chat_id, login)
    token_in_db = get_token_by_chat_id(chat_id, session)
    if token_in_db:
        token_in_db.token = token_table.token
    else:
        session.add(token_table)
    session.commit()
    return token_table.token

def delete_token(data: dict, session):
    try:
        chat_id = str(data["chat_id"])  # Приводим к строке для надежности
        token_in_db = get_token_by_chat_id(chat_id, session)
        if not token_in_db:
            logger.info(f"Токен для chat_id {chat_id} не найден, удаление не требуется")
            return False

        session.delete(token_in_db)
        session.commit()
        logger.info(f"Токен для chat_id {chat_id} успешно удален")
        return True

    except Exception as e:
        session.rollback()  # Откатываем изменения при ошибке
        logger.error(f"Ошибка при удалении токена для chat_id {data.get('chat_id')}: {str(e)}")
        raise  # Пробрасываем исключение дальше


def verify_token(chat_id: str, session):
    token_in_db = get_token_by_chat_id(chat_id, session)
    if token_in_db:
        login = token_in_db.verify_token()
        logger.info(f"LOGIN = {login }")
        if login:
            return login
    return None

def get_all_tokens(session) -> Optional[List[Token]]:
    return session.query(Token).all()





