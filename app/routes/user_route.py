from fastapi import APIRouter, HTTPException, status, Depends, Request
from database.database import get_session
from interaction_servise import user_interaction
from interaction_servise import token_interaction
from object_servise.user import User, UserResponse
from object_servise.token import Token, TokenResponse
from pydantic import EmailStr, ValidationError
from fastapi import FastAPI, Query, Depends

user_route = APIRouter(tags=['User'])


@user_route.post("/login")
async def login_post(data: UserResponse, session=Depends(get_session)):
    login = data.login
    password = data.password
    chat_id = data.chat_id

    user_in_db = user_interaction.get_user_by_login(login, session)
    if not user_in_db:
        return {"error": "User not found"}, 404  # Пользователь не найден

    check_user = user_interaction.autorization_user(user_in_db, password)
    if not check_user:
        return {"error": "Invalid credentials"}, 401  # Неверные данные

    token = token_interaction.create_access_token({"chat_id": chat_id, "login": login}, session)

    return {"token": token}, 200  # Возвращаем токен


from fastapi import HTTPException, status


@user_route.post("/register")
async def register_post(data: UserResponse, session=Depends(get_session)):
    login = data.login
    password = data.password

    # Проверка существования пользователя
    if user_interaction.get_user_by_login(login, session):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,  # 400 лучше для "уже существует"
            detail="User already exists"
        )

    # Попытка создания
    try:
        create_check = user_interaction.create_user(
            UserResponse(login=login, password=password),
            session
        )

        if not create_check:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,  # 422 для ошибок валидации
                detail="Invalid email or password format (6+ chars, 1 letter, 1 digit)"
            )
        else:
            return create_check

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e.errors())}"  # Включаем детали ошибки в ответ
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(e)}"
        )


@user_route.get("/token")
async def token_get(chat_id: str = Query(...), session=Depends(get_session)):
    login = token_interaction.verify_token(chat_id, session)
    if login:
        return {"login": login}
    return {"login": None}, status.HTTP_401_UNAUTHORIZED

@user_route.delete("/logout")
async def logout_delete_token(
    chat_id: str = Query(..., description="ID чата пользователя"),
    session=Depends(get_session)
):
    try:
        check_delete = token_interaction.delete_token({"chat_id": chat_id}, session)
        if check_delete:
            return {
                "status": "success_logout"
            }
        else:
            return {
                "status": "success_not_login"
            }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout"
        )

